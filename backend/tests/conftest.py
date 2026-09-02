"""
Shared pytest fixtures for all backend tests.
"""

import os
import tempfile

_db_file = os.path.join(tempfile.gettempdir(), "c9_erp_test.db")
os.environ.setdefault("JWT_SECRET", "test-secret-key-not-for-production")
os.environ["DATABASE_URL"] = f"sqlite:///{_db_file}"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from main import app
from app.core.database import Base, get_db
from app.models import (
    User, Role, Permission, RolePermission, InventoryItem,
    InventoryCategory, Vendor, Order, OrderItem, OrderTimeline,
    InventoryTransaction, ApprovalRule, Document, Settings,
)
from decimal import Decimal
from app.core.auth import hash_password, create_access_token
from app.services.rate_limiter import rate_limiter


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    rate_limiter.reset()


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(
        f"sqlite:///{_db_file}",
        connect_args={"check_same_thread": False},
        poolclass=NullPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_db(test_engine):
    """Clean all data between tests (keep schema)."""
    Base.metadata.create_all(bind=test_engine)
    with test_engine.connect() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
        conn.commit()
    yield


@pytest.fixture
def db_session(test_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def test_client(test_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.fixture
def client(test_client):
    return test_client


@pytest.fixture
def transactional_db(test_engine):
    """Provide an isolated session per test using SAVEPOINT-based rollback.

    The session begins a transaction; any data inserted via this session is
    rolled back at teardown, so tests don't see each other's state and we
    avoid the cost of ``DELETE FROM every_table`` between every test.

    The session is also wired up as ``get_db`` so HTTP clients see the same
    transactional state.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(
        bind=connection,
        autoflush=False,
        autocommit=False,
        join_transaction_mode="create_savepoint",
    )
    session = TestingSessionLocal()

    def override_get_db():
        try:
            yield session
        finally:
            # Don't close here — the fixture owns the lifecycle.
            pass

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield session
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()
        app.dependency_overrides.pop(get_db, None)


def create_test_roles_and_perms(db, extra_codes=None):
    """Create standard roles and permissions for testing.

    The Admin role receives EVERY permission listed here and in ``extra_codes``
    (via the loop below), so tests that exercise the full order lifecycle and
    vendor CRUD pass with the Phase 0.2 ``require_permission`` guards.
    """
    all_codes = extra_codes or []
    # Mirrors the production permission set in setup_firstrun.py / seed_data.py,
    # plus every code referenced by order/vendor/inventory routers.
    base_codes = [
        "dashboard.view",
        "vendors.create", "vendors.edit", "vendors.delete",
        "inventory.create", "inventory.edit", "inventory.dispatch", "inventory.restock",
        "orders.create", "orders.approve", "orders.cancel", "orders.dispatch",
        "orders.deliver", "orders.close", "orders.return", "orders.manage",
        "users.manage", "reports.view",
    ]
    for code in set(base_codes + all_codes):
        if not db.query(Permission).filter(Permission.code == code).first():
            db.add(Permission(code=code, description=code))
    db.flush()

    admin_role = Role(name="Admin", description="Admin")
    manager_role = Role(name="Manager", description="Manager")
    warehouse_role = Role(name="Warehouse User", description="Warehouse")
    viewer_role = Role(name="Viewer", description="Viewer")
    db.add_all([admin_role, manager_role, warehouse_role, viewer_role])
    db.flush()

    perms = db.query(Permission).all()
    for perm in perms:
        db.add(RolePermission(role_id=admin_role.id, permission_id=perm.id))
        if perm.code in ["orders.create", "orders.approve", "inventory.dispatch"]:
            db.add(RolePermission(role_id=manager_role.id, permission_id=perm.id))
        if perm.code == "inventory.dispatch":
            db.add(RolePermission(role_id=warehouse_role.id, permission_id=perm.id))

    db.commit()
    return admin_role, manager_role, warehouse_role, viewer_role


def create_test_user(db, email="test@example.com", password="testpass123", role=None):
    """Create a test user."""
    user = User(
        full_name="Test User",
        email=email,
        password_hash=hash_password(password),
        is_active=True,
    )
    db.add(user)
    db.flush()
    if role:
        user.role_id = role.id
    db.commit()
    db.refresh(user)
    return user


def login_as(client, email="test@example.com", password="testpass123"):
    """Return auth headers for a test user."""
    response = client.post("/auth/login", json={
        "email": email,
        "password": password,
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_test_vendor(db, name="Test Vendor", email="vendor@test.com", allow_portal=False):
    """Create a test vendor."""
    vendor = Vendor(name=name, name_normalized=name.lower(), email=email, is_active=True, allow_portal=allow_portal)
    db.add(vendor)
    db.commit()
    return vendor


def create_test_inventory_item(db, name="Test Item", sku="TST-001",
                                quantity=100, min_quantity=10):
    """Create a test inventory item."""
    category = InventoryCategory(name="Test Category")
    db.add(category)
    db.flush()
    item = InventoryItem(
        name=name,
        sku=sku,
        description="Test description",
        category_id=category.id,
        current_quantity=Decimal(str(quantity)),
        reserved_quantity=Decimal("0"),
        minimum_quantity=Decimal(str(min_quantity)),
        item_type="consumable",
        is_active=True,
    )
    db.add(item)
    db.commit()
    return item
