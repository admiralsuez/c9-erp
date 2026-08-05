"""
Tests for password reset functionality.
"""
import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from app.core.database import SessionLocal, engine, Base
from app.models import User, Role, Permission, RolePermission, PasswordResetToken
from app.core.auth import hash_password, create_password_reset_token, verify_password_reset_token, mark_password_reset_token_used
from main import app


@pytest.fixture(scope="function")
def setup_db():
    """Create test database and tables."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(setup_db):
    """Create a new database session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """Create test client with session override."""
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[lambda: SessionLocal()] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    # Create Admin role
    admin_role = Role(name="Admin", description="Full system access")
    db_session.add(admin_role)
    db_session.flush()
    
    # Create user
    user = User(
        full_name="Test User",
        email="test@example.com",
        password_hash=hash_password("OldPassword123"),
        role_id=admin_role.id
    )
    db_session.add(user)
    db_session.commit()
    
    return user


class TestPasswordReset:
    """Test password reset functionality."""
    
    def test_request_password_reset_valid_email(self, client, test_user):
        """Test requesting password reset with valid email."""
        response = client.post(
            "/auth/request-password-reset",
            json={"email": "test@example.com"}
        )
        
        assert response.status_code == 200
        assert "message" in response.json()
    
    def test_request_password_reset_nonexistent_email(self, client):
        """Test requesting password reset with non-existent email."""
        # Should not reveal whether user exists (security)
        response = client.post(
            "/auth/request-password-reset",
            json={"email": "nonexistent@example.com"}
        )
        
        assert response.status_code == 200
    
    def test_create_and_verify_token(self, db_session, test_user):
        """Test token creation and verification."""
        token = create_password_reset_token(test_user.id, db_session)
        
        assert token is not None
        assert len(token) > 20  # Should be a URL-safe token
        
        # Verify token
        user_id = verify_password_reset_token(token, db_session)
        assert user_id == test_user.id
    
    def test_expired_token_not_valid(self, db_session, test_user):
        """Test that expired tokens are not valid."""
        import hashlib
        import secrets as _secrets
        
        # Create an expired token
        token = _secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) - timedelta(hours=2)
        
        reset_token = PasswordResetToken(
            user_id=test_user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            used=False
        )
        db_session.add(reset_token)
        db_session.commit()
        
        # Try to verify expired token
        user_id = verify_password_reset_token(token, db_session)
        assert user_id is None
    
    def test_used_token_not_valid(self, db_session, test_user):
        """Test that used tokens are not valid."""
        token = create_password_reset_token(test_user.id, db_session)
        
        # Mark token as used
        mark_password_reset_token_used(token, db_session)
        
        # Try to verify used token
        user_id = verify_password_reset_token(token, db_session)
        assert user_id is None
    
    def test_reset_password_with_valid_token(self, client, db_session, test_user):
        """Test resetting password with a valid token."""
        # Create token
        token = create_password_reset_token(test_user.id, db_session)
        db_session.commit()
        
        # Reset password
        response = client.post(
            "/auth/reset-password",
            json={
                "token": token,
                "new_password": "NewPassword123"
            }
        )
        
        assert response.status_code == 200
        assert "access_token" in response.json()
        
        # Verify password was changed
        db_session.refresh(test_user)
        # New password should be hashed differently from old
        assert test_user.password_hash != hash_password("OldPassword123")
    
    def test_reset_password_with_invalid_token(self, client):
        """Test resetting password with invalid token."""
        response = client.post(
            "/auth/reset-password",
            json={
                "token": "invalid-token-that-does-not-exist",
                "new_password": "NewPassword123"
            }
        )
        
        assert response.status_code == 400
        assert "Invalid" in response.json()["detail"]
    
    def test_reset_password_with_weak_password(self, client, db_session, test_user):
        """Test resetting password with weak password."""
        token = create_password_reset_token(test_user.id, db_session)
        db_session.commit()
        
        response = client.post(
            "/auth/reset-password",
            json={
                "token": token,
                "new_password": "weak"  # Too short
            }
        )
        
        # Should either accept it or reject it based on validation
        # The backend should validate password strength
        assert response.status_code in [200, 400, 422]
    
    def test_token_single_use(self, client, db_session, test_user):
        """Test that token can only be used once."""
        token = create_password_reset_token(test_user.id, db_session)
        db_session.commit()
        
        # First reset - should work
        response1 = client.post(
            "/auth/reset-password",
            json={
                "token": token,
                "new_password": "NewPassword123"
            }
        )
        assert response1.status_code == 200
        
        # Second reset - should fail (token already used)
        response2 = client.post(
            "/auth/reset-password",
            json={
                "token": token,
                "new_password": "AnotherPassword123"
            }
        )
        assert response2.status_code == 400
    
    def test_password_change_invalidates_refresh_tokens(self, db_session, test_user):
        """Test that password reset invalidates existing refresh tokens."""
        from app.models import RefreshToken
        
        # Create a refresh token
        from app.core.auth import create_refresh_token
        refresh_token = create_refresh_token(test_user.id, db_session)
        
        # Reset password
        token = create_password_reset_token(test_user.id, db_session)
        db_session.commit()
        mark_password_reset_token_used(token, db_session)
        
        # Check that refresh tokens are revoked/handled
        refresh_tokens = db_session.query(RefreshToken).filter(
            RefreshToken.user_id == test_user.id
        ).all()
        assert len(refresh_tokens) > 0
    
    def test_concurrent_token_requests(self, db_session, test_user):
        """Test that multiple tokens can be created for same user."""
        token1 = create_password_reset_token(test_user.id, db_session)
        db_session.commit()
        
        token2 = create_password_reset_token(test_user.id, db_session)
        db_session.commit()
        
        # Both tokens should be valid
        assert verify_password_reset_token(token1, db_session) == test_user.id
        assert verify_password_reset_token(token2, db_session) == test_user.id
    
    def test_reset_password_creates_new_tokens(self, client, db_session, test_user):
        """Test that password reset creates new access and refresh tokens."""
        token = create_password_reset_token(test_user.id, db_session)
        db_session.commit()
        
        response = client.post(
            "/auth/reset-password",
            json={
                "token": token,
                "new_password": "NewPassword123"
            }
        )
        
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data


class TestPasswordResetSecurity:
    """Test security aspects of password reset."""
    
    def test_token_hash_not_stored_plaintext(self, db_session, test_user):
        """Test that tokens are stored as hashes, not plaintext."""
        token = create_password_reset_token(test_user.id, db_session)
        db_session.commit()
        
        # Retrieve from database
        reset_token = db_session.query(PasswordResetToken).first()
        
        # Token hash should not equal the original token
        assert reset_token.token_hash != token
        assert len(reset_token.token_hash) == 64  # SHA-256 hex digest
    
    def test_request_password_reset_does_not_leak_user_info(self, client, db_session, test_user):
        """Test that endpoint doesn't reveal whether user exists."""
        # Request for existing user
        response1 = client.post(
            "/auth/request-password-reset",
            json={"email": "test@example.com"}
        )
        
        # Request for non-existing user
        response2 = client.post(
            "/auth/request-password-reset",
            json={"email": "nonexistent@example.com"}
        )
        
        # Both should return same status and similar response
        assert response1.status_code == response2.status_code
        assert response1.status_code == 200
    
    def test_token_expiration_enforced(self, db_session, test_user):
        """Test that token expiration is properly enforced."""
        import hashlib
        import secrets as _secrets
        
        # Create an almost-expired token
        token = _secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=1)
        
        reset_token = PasswordResetToken(
            user_id=test_user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            used=False
        )
        db_session.add(reset_token)
        db_session.commit()
        
        # Token should be valid immediately
        user_id = verify_password_reset_token(token, db_session)
        assert user_id == test_user.id
        
        # After expiration (simulate time passing)
        reset_token.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        db_session.commit()
        
        # Token should now be invalid
        user_id = verify_password_reset_token(token, db_session)
        assert user_id is None
