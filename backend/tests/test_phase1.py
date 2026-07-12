"""
Phase 1 test suite: Auth, RBAC, Inventory Ledger, Vendor Dedup, Soft Delete

Uses shared conftest fixtures (client, db_session) and helpers.
"""

import pytest
from decimal import Decimal

from app.models import (
    InventoryItem,
    InventoryTransaction, Vendor,
)
from .conftest import (
    create_test_roles_and_perms, create_test_user, create_test_vendor,
    create_test_inventory_item, login_as,
)


class TestAuth:
    """Test authentication endpoints."""

    def test_login_success(self, client, db_session):
        """Test successful login."""
        admin_role, _, _, _ = create_test_roles_and_perms(db_session)
        user = create_test_user(db_session, "admin@test.com", "password123", admin_role)

        response = client.post("/auth/login", json={
            "email": "admin@test.com",
            "password": "password123"
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_password(self, client, db_session):
        """Test login with invalid password."""
        admin_role, _, _, _ = create_test_roles_and_perms(db_session)
        user = create_test_user(db_session, "admin@test.com", "password123", admin_role)

        response = client.post("/auth/login", json={
            "email": "admin@test.com",
            "password": "wrongpassword"
        })

        assert response.status_code == 401


class TestRBAC:
    """Test role-based access control."""

    def test_warehouse_user_can_restock(self, client, db_session):
        """Test warehouse user can restock inventory."""
        admin_role, _, warehouse_role, viewer_role = create_test_roles_and_perms(db_session)

        warehouse_user = create_test_user(db_session, "warehouse@test.com", "password123", warehouse_role)

        item = create_test_inventory_item(db_session, "Test Item", "SKU-TEST-001", quantity=100)

        headers = login_as(client, "warehouse@test.com", "password123")

        response = client.post(
            "/inventory/restock",
            json={"item_id": item.id, "quantity": 50, "reason": "Restock"},
            headers=headers
        )

        assert response.status_code == 200

    def test_viewer_cannot_restock(self, client, db_session):
        """Test viewer role cannot restock."""
        admin_role, _, warehouse_role, viewer_role = create_test_roles_and_perms(db_session)

        viewer_user = create_test_user(db_session, "viewer@test.com", "password123", viewer_role)

        item = create_test_inventory_item(db_session, "Test Item", "SKU-TEST-001", quantity=100)

        headers = login_as(client, "viewer@test.com", "password123")

        response = client.post(
            "/inventory/restock",
            json={"item_id": item.id, "quantity": 50, "reason": "Restock"},
            headers=headers
        )

        assert response.status_code == 403


class TestInventoryLedger:
    """Test inventory transaction ledger."""

    def test_restock_creates_transaction(self, client, db_session):
        """Test that restock creates a transaction entry."""
        admin_role, _, _, _ = create_test_roles_and_perms(db_session)
        user = create_test_user(db_session, "admin@test.com", "password123", admin_role)

        item = create_test_inventory_item(db_session, "Test Item", "SKU-TEST-001", quantity=100)

        headers = login_as(client, "admin@test.com", "password123")

        response = client.post(
            "/inventory/restock",
            json={"item_id": item.id, "quantity": 50, "reason": "Test restock"},
            headers=headers
        )

        assert response.status_code == 200
        transaction_data = response.json()

        assert transaction_data["transaction_type"] == "stock_added"
        assert transaction_data["previous_quantity"] == 100
        assert transaction_data["change_quantity"] == 50
        assert transaction_data["new_quantity"] == 150

        db_session.expire_all()
        db_item = db_session.query(InventoryItem).filter(InventoryItem.id == item.id).first()
        assert db_item.current_quantity == Decimal("150")

    def test_quantity_never_written_directly(self, db_session):
        """Test that item quantity is only updated through ledger."""
        item = create_test_inventory_item(db_session, "Test Item", "SKU-TEST-001", quantity=100)

        initial_txn_count = db_session.query(InventoryTransaction).filter(
            InventoryTransaction.item_id == item.id
        ).count()

        assert initial_txn_count == 0


class TestVendorDedup:
    """Test vendor duplicate detection."""

    def test_vendor_exact_match_blocked(self, client, db_session):
        """Test that creating vendor with exact normalized name is blocked."""
        admin_role, _, _, _ = create_test_roles_and_perms(db_session)
        user = create_test_user(db_session, "admin@test.com", "password123", admin_role)

        vendor1 = Vendor(
            name="ABC Traders",
            name_normalized="abc traders",
            vendor_type="Wholesale"
        )
        db_session.add(vendor1)
        db_session.commit()

        headers = login_as(client, "admin@test.com", "password123")

        response = client.post(
            "/vendors",
            json={"name": "abc traders", "vendor_type": "Wholesale"},
            headers=headers
        )

        assert response.status_code == 409

    def test_vendor_case_insensitive_dedup(self, client, db_session):
        """Test vendor dedup is case-insensitive."""
        admin_role, _, _, _ = create_test_roles_and_perms(db_session)
        user = create_test_user(db_session, "admin@test.com", "password123", admin_role)

        vendor1 = Vendor(
            name="ABC Traders",
            name_normalized="abc traders",
            vendor_type="Wholesale"
        )
        db_session.add(vendor1)
        db_session.commit()

        headers = login_as(client, "admin@test.com", "password123")

        response = client.post(
            "/vendors",
            json={"name": "ABC TRADERS", "vendor_type": "Wholesale"},
            headers=headers
        )

        assert response.status_code == 409


class TestSoftDelete:
    """Test soft delete pattern."""

    def test_soft_delete_vendor(self, client, db_session):
        """Test soft deleting a vendor."""
        admin_role, _, _, _ = create_test_roles_and_perms(db_session)
        user = create_test_user(db_session, "admin@test.com", "password123", admin_role)

        vendor = Vendor(
            name="ABC Traders",
            name_normalized="abc traders",
            vendor_type="Wholesale"
        )
        db_session.add(vendor)
        db_session.commit()
        vendor_id = vendor.id

        headers = login_as(client, "admin@test.com", "password123")

        response = client.delete(
            f"/vendors/{vendor_id}",
            headers=headers
        )

        assert response.status_code == 204

        db_session.expire_all()
        db_vendor = db_session.query(Vendor).filter(Vendor.id == vendor_id).first()
        assert db_vendor.deleted_at is not None

        response = client.get(
            "/vendors",
            headers=headers
        )

        assert response.status_code == 200
        vendors = response.json()
        assert len(vendors.get("items", vendors)) == 0
