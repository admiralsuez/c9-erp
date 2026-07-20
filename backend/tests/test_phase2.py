"""
Phase 2 test suite: Orders + Reservation + Approval Matrix + Dispatch + Timeline

Uses shared conftest fixtures (client, db_session) and helpers.
"""

import pytest
from decimal import Decimal

from app.models import (
    InventoryItem, Order, ApprovalRule,
)
from .conftest import (
    create_test_roles_and_perms, create_test_user, create_test_vendor,
    create_test_inventory_item, login_as,
)


class TestOrderStateMachine:
    """Test order state machine transitions."""

    def test_create_order_in_draft(self, client, db_session):
        """Test creating an order in Draft status."""
        admin_role, _, _, _ = create_test_roles_and_perms(db_session)
        user = create_test_user(db_session, "admin@test.com", "password", admin_role)
        vendor = create_test_vendor(db_session)
        item = create_test_inventory_item(db_session, "Widget", "SKU-001")

        headers = login_as(client, "admin@test.com", "password")

        response = client.post(
            "/orders",
            json={
                "vendor_id": vendor.id,
                "items": [{"item_id": item.id, "quantity_ordered": 50}],
                "remarks": "Test order"
            },
            headers=headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "draft"
        assert data["order_number"].startswith("HO-ORD-") or data["order_number"].startswith("ORD-")

    def test_draft_to_pending_requisition(self, client, db_session):
        """Test Draft -> Pending Requisition transition."""
        admin_role, _, _, _ = create_test_roles_and_perms(db_session)
        user = create_test_user(db_session, "admin@test.com", "password", admin_role)
        vendor = create_test_vendor(db_session)
        item = create_test_inventory_item(db_session, "Widget", "SKU-001")

        headers = login_as(client, "admin@test.com", "password")

        response = client.post(
            "/orders",
            json={
                "vendor_id": vendor.id,
                "items": [{"item_id": item.id, "quantity_ordered": 50}],
            },
            headers=headers
        )
        order_id = response.json()["id"]

        response = client.post(
            f"/orders/{order_id}/submit-requisition?approver_id={user.id}",
            headers=headers
        )

        assert response.status_code == 200
        assert response.json()["status"] == "pending_requisition"

    def test_invalid_state_transition(self, client, db_session):
        """Test that invalid transitions are blocked."""
        admin_role, _, _, _ = create_test_roles_and_perms(db_session)
        user = create_test_user(db_session, "admin@test.com", "password", admin_role)
        vendor = create_test_vendor(db_session)
        item = create_test_inventory_item(db_session, "Widget", "SKU-001")

        headers = login_as(client, "admin@test.com", "password")

        response = client.post(
            "/orders",
            json={
                "vendor_id": vendor.id,
                "items": [{"item_id": item.id, "quantity_ordered": 50}],
            },
            headers=headers
        )
        order_id = response.json()["id"]

        response = client.post(
            f"/orders/{order_id}/dispatch",
            json={"items": [{"item_id": item.id, "quantity": 50}], "partial": False},
            headers=headers
        )

        assert response.status_code == 400


class TestReservation:
    """Test inventory reservation logic."""

    def _progress_to_approved(self, client, db_session, user, order_id):
        """Helper: move an order through to approved state."""
        client.post(
            f"/orders/{order_id}/submit-requisition?approver_id={user.id}",
            headers=login_as(client, "admin@test.com", "password")
        )
        client.post(
            f"/orders/{order_id}/upload-signed",
            files={"file": ("signed.pdf", b"dummy", "application/pdf")},
            headers=login_as(client, "admin@test.com", "password")
        )

    def test_approve_reserves_stock(self, client, db_session):
        """Test that approving order reserves stock."""
        admin_role, _, _, _ = create_test_roles_and_perms(db_session)
        user = create_test_user(db_session, "admin@test.com", "password", admin_role)
        vendor = create_test_vendor(db_session)
        item = create_test_inventory_item(db_session, "Widget", "SKU-001", quantity=100)

        headers = login_as(client, "admin@test.com", "password")

        response = client.post(
            "/orders",
            json={
                "vendor_id": vendor.id,
                "items": [{"item_id": item.id, "quantity_ordered": 50}],
            },
            headers=headers
        )
        order_id = response.json()["id"]

        self._progress_to_approved(client, db_session, user, order_id)

        response = client.post(
            f"/orders/{order_id}/approve",
            headers=headers
        )
        assert response.status_code == 200

        db_session.expire_all()
        db_item = db_session.query(InventoryItem).filter(InventoryItem.id == item.id).first()
        assert db_item.reserved_quantity == Decimal("50")

    def test_insufficient_stock_blocks_approval(self, client, db_session):
        """Test that order creation fails if stock is insufficient (reserved on creation)."""
        admin_role, _, _, _ = create_test_roles_and_perms(db_session)
        user = create_test_user(db_session, "admin@test.com", "password", admin_role)
        vendor = create_test_vendor(db_session)
        item = create_test_inventory_item(db_session, "Widget", "SKU-001", quantity=30)

        headers = login_as(client, "admin@test.com", "password")

        response = client.post(
            "/orders",
            json={
                "vendor_id": vendor.id,
                "items": [{"item_id": item.id, "quantity_ordered": 50}],
            },
            headers=headers
        )

        assert response.status_code == 409
        detail = response.json()["detail"]
        if isinstance(detail, dict):
            assert "Insufficient stock" in detail["message"]
        else:
            assert "Insufficient stock" in str(detail)

    def test_cancel_releases_reservation(self, client, db_session):
        """Test that cancelling order releases reservation."""
        admin_role, _, _, _ = create_test_roles_and_perms(db_session)
        user = create_test_user(db_session, "admin@test.com", "password", admin_role)
        vendor = create_test_vendor(db_session)
        item = create_test_inventory_item(db_session, "Widget", "SKU-001", quantity=100)

        headers = login_as(client, "admin@test.com", "password")

        response = client.post(
            "/orders",
            json={
                "vendor_id": vendor.id,
                "items": [{"item_id": item.id, "quantity_ordered": 50}],
            },
            headers=headers
        )
        order_id = response.json()["id"]

        self._progress_to_approved(client, db_session, user, order_id)
        client.post(f"/orders/{order_id}/approve", headers=headers)

        response = client.post(
            f"/orders/{order_id}/cancel",
            headers=headers
        )
        assert response.status_code == 200

        db_item = db_session.query(InventoryItem).filter(InventoryItem.id == item.id).first()
        assert db_item.reserved_quantity == Decimal("0")


class TestDispatch:
    """Test dispatch logic."""

    def test_dispatch_creates_ledger_entry(self, client, db_session):
        """Test that dispatch creates inventory transaction."""
        admin_role, _, _, _ = create_test_roles_and_perms(db_session)
        user = create_test_user(db_session, "admin@test.com", "password", admin_role)
        vendor = create_test_vendor(db_session)
        item = create_test_inventory_item(db_session, "Widget", "SKU-001", quantity=100)

        headers = login_as(client, "admin@test.com", "password")

        response = client.post(
            "/orders",
            json={
                "vendor_id": vendor.id,
                "items": [{"item_id": item.id, "quantity_ordered": 50}],
            },
            headers=headers
        )
        order_id = response.json()["id"]

        client.post(f"/orders/{order_id}/submit-requisition?approver_id={user.id}", headers=headers)
        client.post(
            f"/orders/{order_id}/upload-signed",
            files={"file": ("signed.pdf", b"dummy", "application/pdf")},
            headers=headers
        )
        client.post(f"/orders/{order_id}/approve", headers=headers)

        response = client.post(
            f"/orders/{order_id}/dispatch",
            json={"items": [{"item_id": item.id, "quantity": 50}], "partial": False},
            headers=headers
        )
        assert response.status_code == 200

        db_session.expire_all()
        db_item = db_session.query(InventoryItem).filter(InventoryItem.id == item.id).first()
        assert db_item.current_quantity == Decimal("50")
        assert db_item.reserved_quantity == Decimal("0")

    def test_partial_dispatch(self, client, db_session):
        """Test partial dispatch."""
        admin_role, _, _, _ = create_test_roles_and_perms(db_session)
        user = create_test_user(db_session, "admin@test.com", "password", admin_role)
        vendor = create_test_vendor(db_session)
        item = create_test_inventory_item(db_session, "Widget", "SKU-001", quantity=100)

        headers = login_as(client, "admin@test.com", "password")

        response = client.post(
            "/orders",
            json={
                "vendor_id": vendor.id,
                "items": [{"item_id": item.id, "quantity_ordered": 50}],
            },
            headers=headers
        )
        order_id = response.json()["id"]

        client.post(f"/orders/{order_id}/submit-requisition?approver_id={user.id}", headers=headers)
        client.post(
            f"/orders/{order_id}/upload-signed",
            files={"file": ("signed.pdf", b"dummy", "application/pdf")},
            headers=headers
        )
        client.post(f"/orders/{order_id}/approve", headers=headers)

        response = client.post(
            f"/orders/{order_id}/dispatch",
            json={"items": [{"item_id": item.id, "quantity": 30}], "partial": True},
            headers=headers
        )
        assert response.status_code == 200

        db_session.expire_all()
        db_item = db_session.query(InventoryItem).filter(InventoryItem.id == item.id).first()
        assert db_item.current_quantity == Decimal("70")


class TestApprovalMatrix:
    """Test approval matrix routing."""

    def test_approval_matrix_blocks_unauthorized_approver(self, client, db_session):
        """Test that non-matching users are blocked by approval matrix."""
        admin_role, manager_role, _, _ = create_test_roles_and_perms(db_session, extra_codes=["orders.create", "orders.approve"])
        manager = create_test_user(db_session, "manager@test.com", "password", manager_role)

        rule = ApprovalRule(
            name="High quantity rule",
            rule_type="quantity",
            condition_json={"min_quantity": 100},
            approver_role_id=admin_role.id,
            priority=0
        )
        db_session.add(rule)

        vendor = create_test_vendor(db_session)
        item = create_test_inventory_item(db_session, "Widget", "SKU-001", quantity=500)
        db_session.commit()

        headers = login_as(client, "manager@test.com", "password")

        response = client.post(
            "/orders",
            json={
                "vendor_id": vendor.id,
                "items": [{"item_id": item.id, "quantity_ordered": 150}],
            },
            headers=headers
        )
        order_id = response.json()["id"]

        client.post(f"/orders/{order_id}/submit-requisition?approver_id={manager.id}", headers=headers)
        client.post(
            f"/orders/{order_id}/upload-signed",
            files={"file": ("signed.pdf", b"dummy", "application/pdf")},
            headers=headers
        )

        response = client.post(
            f"/orders/{order_id}/approve",
            headers=headers
        )
        assert response.status_code == 403


class TestOrderTimeline:
    """Test order timeline tracking."""

    def test_timeline_tracks_transitions(self, client, db_session):
        """Test that timeline tracks all state transitions."""
        admin_role, _, _, _ = create_test_roles_and_perms(db_session)
        user = create_test_user(db_session, "admin@test.com", "password", admin_role)
        vendor = create_test_vendor(db_session)
        item = create_test_inventory_item(db_session, "Widget", "SKU-001")

        headers = login_as(client, "admin@test.com", "password")

        response = client.post(
            "/orders",
            json={
                "vendor_id": vendor.id,
                "items": [{"item_id": item.id, "quantity_ordered": 50}],
            },
            headers=headers
        )
        order_id = response.json()["id"]

        response = client.get(
            f"/orders/{order_id}/timeline",
            headers=headers
        )

        assert response.status_code == 200
        timeline = response.json()
        assert len(timeline) > 0
        assert timeline[0]["action"] == "created"
