"""
Phase 0 test suite: Inventory service (row-locking ledger), order state machine,
vendor portal magic-link auth, reservation oversell prevention.
"""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.database import Base
from app.models import (
    User, Role, Permission, RolePermission, InventoryItem,
    InventoryCategory, Vendor, Order, OrderItem, OrderTimeline,
    InventoryTransaction,
)
from app.services.inventory_service import (
    restock_item as svc_restock,
    adjust_item as svc_adjust,
)
from .conftest import (
    create_test_roles_and_perms, create_test_user, create_test_vendor,
    create_test_inventory_item, login_as,
)


class TestInventoryServiceLedger:
    """Test that all inventory operations go through the service (row-locking)."""

    def test_restock_increases_quantity(self, db_session: Session):
        item = create_test_inventory_item(db_session, sku="RS-001", quantity=50)
        user = create_test_user(db_session)
        svc_restock(db_session, item.id, Decimal("10"), "Restock test", user.id)

        db_session.refresh(item)
        assert item.current_quantity == Decimal("60")

        txn = db_session.query(InventoryTransaction).filter(
            InventoryTransaction.item_id == item.id,
            InventoryTransaction.transaction_type == "stock_added",
        ).first()
        assert txn is not None
        assert txn.change_quantity == Decimal("10")

    def test_adjust_quantity(self, db_session: Session):
        item = create_test_inventory_item(db_session, sku="RS-006", quantity=50)
        user = create_test_user(db_session)
        svc_adjust(db_session, item.id, Decimal("75"), "Adjustment test", user.id)

        db_session.refresh(item)
        assert item.current_quantity == Decimal("75")

    def test_reserve_oversell_blocked(self, db_session: Session):
        from app.services.inventory_service import reserve_stock

        item = create_test_inventory_item(db_session, sku="RS-003", quantity=10)
        user = create_test_user(db_session)
        vendor = create_test_vendor(db_session)
        order = Order(vendor_id=vendor.id, created_by=user.id, status="approved", order_number="OVR-001")
        db_session.add(order)
        db_session.flush()
        oi = OrderItem(order_id=order.id, item_id=item.id, quantity_ordered=Decimal("99"))
        db_session.add(oi)
        db_session.commit()

        errors = reserve_stock(db_session, [oi], user.id)
        assert errors, "Expected reservation errors but got none"

    def test_full_reserve_release(self, db_session: Session):
        from app.services.inventory_service import reserve_stock, release_reservation

        item = create_test_inventory_item(db_session, sku="RS-004", quantity=50)
        user = create_test_user(db_session)
        vendor = create_test_vendor(db_session)
        order = Order(vendor_id=vendor.id, created_by=user.id, status="approved", order_number="REL-001")
        db_session.add(order)
        db_session.flush()
        oi = OrderItem(order_id=order.id, item_id=item.id, quantity_ordered=Decimal("20"))
        db_session.add(oi)
        db_session.commit()

        errors = reserve_stock(db_session, [oi], user.id)
        assert errors == []
        db_session.flush()

        db_session.refresh(item)
        assert item.reserved_quantity == Decimal("20")

        release_reservation(db_session, [oi])
        db_session.flush()
        db_session.refresh(item)
        assert item.reserved_quantity == Decimal("0")

    def test_dispatch_moves_stock(self, db_session: Session):
        from app.services.inventory_service import reserve_stock, dispatch_stock

        item = create_test_inventory_item(db_session, sku="RS-005", quantity=100)
        user = create_test_user(db_session)
        vendor = create_test_vendor(db_session)
        order = Order(vendor_id=vendor.id, created_by=user.id, status="approved", order_number="DSP-001")
        db_session.add(order)
        db_session.flush()
        oi = OrderItem(order_id=order.id, item_id=item.id, quantity_ordered=Decimal("10"))
        db_session.add(oi)
        db_session.commit()

        errors = reserve_stock(db_session, [oi], user.id)
        assert errors == []

        dispatch_stock(db_session, [oi], {item.id: 10}, order.id, order.order_number or "TEST", user.id, partial=False)
        db_session.flush()

        db_session.refresh(item)
        assert item.current_quantity == Decimal("90")
        assert item.reserved_quantity == Decimal("0")


class TestOrderStateMachine:
    """Test order lifecycle transitions."""

    def test_full_order_lifecycle(self, client: TestClient, db_session: Session):
        roles = create_test_roles_and_perms(db_session)
        admin_role, *_ = roles
        user = create_test_user(db_session, role=admin_role)
        vendor = create_test_vendor(db_session)
        item = create_test_inventory_item(db_session, sku="OSM-001", quantity=100)
        headers = login_as(client)

        resp = client.post("/orders", json={
            "vendor_id": vendor.id,
            "items": [{"item_id": item.id, "quantity_ordered": 5}],
        }, headers=headers)
        assert resp.status_code == 201
        order_id = resp.json()["id"]
        assert resp.json()["status"] == "draft"

        resp = client.post(f"/orders/{order_id}/submit-requisition?approver_id={user.id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "pending_requisition"

        resp = client.post(
            f"/orders/{order_id}/upload-signed",
            headers=headers,
            files={"file": ("signed.pdf", b"fake-pdf-content", "application/pdf")},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "signed_requisition_uploaded"

        resp = client.post(f"/orders/{order_id}/approve", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "approved"

        resp = client.post(f"/orders/{order_id}/dispatch", json={
            "items": [{"item_id": item.id, "quantity": 5}],
            "partial": False,
        }, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "dispatched"

        resp = client.post(f"/orders/{order_id}/deliver", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "delivered"


class TestRBAC:
    """Test permission enforcement on key endpoints."""

    def test_viewer_cannot_restock(self, client: TestClient, db_session: Session):
        roles = create_test_roles_and_perms(db_session)
        *_, viewer_role = roles
        user = create_test_user(db_session, email="viewer_rbac@test.com", role=viewer_role)
        item = create_test_inventory_item(db_session, sku="RBAC-001")
        headers = login_as(client, email="viewer_rbac@test.com")

        resp = client.post("/inventory/restock", json={
            "item_id": item.id, "quantity": 10, "reason": "test",
        }, headers=headers)
        assert resp.status_code == 403


class TestVendorPortalMagicLink:
    """Test vendor portal magic-link auth flow."""

    def test_magic_link_flow(self, client: TestClient, db_session: Session):
        create_test_vendor(db_session, email="vendor_ml@test.com", allow_portal=True)

        resp = client.post("/vendor-portal/request-magic-link?email=vendor_ml@test.com")
        assert resp.status_code == 200
        assert "magic link" in resp.json()["message"].lower()

    def test_verify_without_request_returns_401(self, client: TestClient):
        resp = client.post("/vendor-portal/verify-magic-link?token=invalid-token")
        assert resp.status_code == 401

    def test_magic_link_full_flow(self, client: TestClient, db_session: Session):
        from datetime import datetime, timezone, timedelta
        from jose import jwt as jose_jwt
        from app.core.config import settings

        vendor = create_test_vendor(db_session, email="vendor_full@test.com", allow_portal=True)

        magic_link_jwt = jose_jwt.encode(
            {"sub": f"vendor:{vendor.id}", "email": vendor.email,
             "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
             "iat": datetime.now(timezone.utc), "type": "vendor_magic_link"},
            settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM,
        )

        resp = client.post(f"/vendor-portal/verify-magic-link?token={magic_link_jwt}")
        assert resp.status_code == 200
        data = resp.json()
        assert "vendor_token" in data
        assert "vendor_id" in data

        session_token = data["vendor_token"]
        auth_header = {"Authorization": f"Bearer {session_token}"}

        resp = client.get("/vendor-portal/dashboard", headers=auth_header)
        assert resp.status_code == 200

    def test_magic_link_disabled_vendor_returns_401(self, client: TestClient, db_session: Session):
        create_test_vendor(db_session, email="no_portal@test.com", allow_portal=False)
        resp = client.post("/vendor-portal/request-magic-link?email=no_portal@test.com")
        assert resp.status_code == 401


class TestEdgeCases:
    """Edge cases for inventory and concurrency."""

    def test_concurrent_oversell_prevention(self, test_engine):
        """Spawn threads that race to reserve stock beyond available quantity.
        Validates row-locking prevents overselling.
        Only meaningful on PostgreSQL (SQLite ignores FOR UPDATE, so skip there).
        """
        if test_engine.dialect.name == "sqlite":
            pytest.skip("SQLite ignores FOR UPDATE — test only meaningful on PostgreSQL")

        import threading
        from sqlalchemy.orm import sessionmaker

        SessionLocal = sessionmaker(bind=test_engine)

        # Setup stock
        s = SessionLocal()
        try:
            item = create_test_inventory_item(s, sku="CONC-001", quantity=10)
            vendor = create_test_vendor(s)
            user = create_test_user(s, email="conc_user@test.com")
        finally:
            s.close()

        n_threads = 5
        each_qty = 3  # 5 × 3 = 15 > 10 → at most 3 can succeed
        barrier = threading.Barrier(n_threads)
        results_lock = threading.Lock()
        successes = 0
        failures = []

        def try_reserve(tid: int):
            nonlocal successes, failures
            session = SessionLocal()
            try:
                order = Order(
                    vendor_id=vendor.id, created_by=user.id,
                    status="approved", order_number=f"CONC-{tid:03d}",
                )
                session.add(order)
                session.flush()
                oi = OrderItem(order_id=order.id, item_id=item.id,
                               quantity_ordered=Decimal(str(each_qty)))
                session.add(oi)
                session.commit()

                barrier.wait()

                errors = reserve_stock(session, [oi], user.id)
                session.commit()
                with results_lock:
                    if errors:
                        failures.extend(errors)
                    else:
                        successes += 1
            except Exception as e:
                with results_lock:
                    failures.append(str(e))
            finally:
                session.close()

        threads = [threading.Thread(target=try_reserve, args=(i,)) for i in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        s = SessionLocal()
        try:
            final_item = s.query(InventoryItem).filter(InventoryItem.id == item.id).first()
            total_reserved = final_item.reserved_quantity
            assert total_reserved <= Decimal("10"), (
                f"Oversell detected: reserved {total_reserved} of 10"
            )
            assert successes <= 3, f"Reserved {successes} orders, expected ≤3"
            assert len(failures) >= n_threads - 3, (
                f"Expected at least {n_threads - 3} failures, got {len(failures)}"
            )
        finally:
            s.close()

    def test_exact_boundary_reservation(self, db_session: Session):
        from app.services.inventory_service import reserve_stock

        item = create_test_inventory_item(db_session, sku="BND-001", quantity=10)
        user = create_test_user(db_session)
        vendor = create_test_vendor(db_session)
        order = Order(vendor_id=vendor.id, created_by=user.id, status="approved", order_number="BND-001")
        db_session.add(order)
        db_session.flush()
        oi = OrderItem(order_id=order.id, item_id=item.id, quantity_ordered=Decimal("10"))
        db_session.add(oi)
        db_session.commit()

        errors = reserve_stock(db_session, [oi], user.id)
        assert errors == []

    def test_multiple_order_reservations_same_item(self, db_session: Session):
        from app.services.inventory_service import reserve_stock

        item = create_test_inventory_item(db_session, sku="MUL-001", quantity=50)
        user = create_test_user(db_session)
        vendor = create_test_vendor(db_session)

        order1 = Order(vendor_id=vendor.id, created_by=user.id, status="approved", order_number="MUL-001")
        order2 = Order(vendor_id=vendor.id, created_by=user.id, status="approved", order_number="MUL-002")
        db_session.add_all([order1, order2])
        db_session.flush()

        oi1 = OrderItem(order_id=order1.id, item_id=item.id, quantity_ordered=Decimal("30"))
        oi2 = OrderItem(order_id=order2.id, item_id=item.id, quantity_ordered=Decimal("30"))
        db_session.add_all([oi1, oi2])
        db_session.commit()

        errors1 = reserve_stock(db_session, [oi1], user.id)
        assert errors1 == []
        db_session.flush()

        errors2 = reserve_stock(db_session, [oi2], user.id)
        assert errors2, "Second reservation should fail due to insufficient available stock"

    def test_cancel_releases_reservation(self, db_session: Session):
        from app.services.inventory_service import reserve_stock, release_reservation

        item = create_test_inventory_item(db_session, sku="CAN-001", quantity=50)
        user = create_test_user(db_session)
        vendor = create_test_vendor(db_session)
        order = Order(vendor_id=vendor.id, created_by=user.id, status="approved", order_number="CAN-001")
        db_session.add(order)
        db_session.flush()
        oi = OrderItem(order_id=order.id, item_id=item.id, quantity_ordered=Decimal("20"))
        db_session.add(oi)
        db_session.commit()

        reserve_stock(db_session, [oi], user.id)
        db_session.flush()
        db_session.refresh(item)
        assert item.reserved_quantity == Decimal("20")

        release_reservation(db_session, [oi])
        db_session.flush()
        db_session.refresh(item)
        assert item.reserved_quantity == Decimal("0")

        # Now another order can reserve the freed stock
        order2 = Order(vendor_id=vendor.id, created_by=user.id, status="approved", order_number="CAN-002")
        db_session.add(order2)
        db_session.flush()
        oi2 = OrderItem(order_id=order2.id, item_id=item.id, quantity_ordered=Decimal("20"))
        db_session.add(oi2)
        db_session.commit()

        errors = reserve_stock(db_session, [oi2], user.id)
        assert errors == []
