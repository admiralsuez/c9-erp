"""
Phase 1.3 test suite: vendor type reassign-on-delete + soft-deleted handling.

Validates the fix for the vendor-type-deletion bug where soft-deleted vendors
were excluded from the reassignment count, leaving them with a dangling FK
to the deleted vendor type.

Endpoints under test (see ``app/routers/vendors.py``):
  - POST /vendors/types/{type_id}/reassign-and-delete?new_type_id=...
  - DELETE /vendors/types/{type_id}
"""
import pytest
from datetime import datetime, timezone

from app.models import (
    Vendor,
    VendorType,
)
from .conftest import (
    create_test_roles_and_perms,
    create_test_user,
    login_as,
)


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TestVendorTypeReassignOnDelete:
    """Verify vendor type reassignment counts all vendors, including soft-deleted."""

    def test_reassign_includes_soft_deleted_vendors(self, client, db_session):
        """When reassigning on delete, soft-deleted vendors must also be moved."""
        admin_role, _, _, _ = create_test_roles_and_perms(db_session)
        create_test_user(db_session, "admin@test.com", "password123", admin_role)

        wholesale = VendorType(name="Wholesale")
        retail = VendorType(name="Retail")
        db_session.add_all([wholesale, retail])
        db_session.flush()
        wholesale_id = wholesale.id
        retail_id = retail.id

        v1 = Vendor(name="V1", name_normalized="v1",
                    vendor_type="Wholesale", vendor_type_id=wholesale_id)
        v2 = Vendor(name="V2", name_normalized="v2",
                    vendor_type="Wholesale", vendor_type_id=wholesale_id)
        v3 = Vendor(name="V3", name_normalized="v3",
                    vendor_type="Wholesale", vendor_type_id=wholesale_id,
                    deleted_at=_utcnow())
        db_session.add_all([v1, v2, v3])
        db_session.commit()

        headers = login_as(client, "admin@test.com", "password123")

        response = client.post(
            f"/vendors/types/{wholesale_id}/reassign-and-delete",
            params={"new_type_id": retail_id},
            headers=headers,
        )
        assert response.status_code == 200, response.text
        body = response.json()

        # Soft-deleted + active all moved; the FK must be released everywhere
        assert body["reassigned_count"] == 3, (
            f"expected 3 (incl. soft-deleted), got {body['reassigned_count']}"
        )

        # Re-query fresh from the DB (the endpoint commits on its own session)
        # rather than refreshing the possibly-stale objects from the fixture.
        fresh = {
            v.id: v
            for v in db_session.query(Vendor).filter(
                Vendor.id.in_([v1.id, v2.id, v3.id])
            ).all()
        }
        for origin in (v1, v2, v3):
            v = fresh[origin.id]
            assert v.vendor_type_id == retail_id, f"{v.name} not reassigned"
            assert v.vendor_type == "Retail", f"{v.name} legacy string not synced"

    def test_plain_delete_clears_fk_on_soft_deleted(self, client, db_session):
        """Plain delete (no reassign) must clear vendor_type_id on soft-deleted vendors."""
        admin_role, _, _, _ = create_test_roles_and_perms(db_session)
        create_test_user(db_session, "admin@test.com", "password123", admin_role)

        wholesale = VendorType(name="Wholesale")
        db_session.add(wholesale)
        db_session.flush()

        deleted = Vendor(name="Old Co", name_normalized="old co",
                         vendor_type="Wholesale", vendor_type_id=wholesale.id,
                         deleted_at=_utcnow())
        db_session.add(deleted)
        db_session.commit()

        headers = login_as(client, "admin@test.com", "password123")

        # No active vendors use the type, so delete succeeds with 204.
        response = client.delete(
            f"/vendors/types/{wholesale.id}",
            headers=headers,
        )
        assert response.status_code == 204, response.text

        db_session.expire_all()
        db_session.refresh(deleted)
        assert deleted.vendor_type_id is None
        assert deleted.vendor_type is None

    def test_plain_delete_blocked_by_active_vendor(self, client, db_session):
        """Plain delete must 409 when an active vendor still uses the type."""
        admin_role, _, _, _ = create_test_roles_and_perms(db_session)
        create_test_user(db_session, "admin@test.com", "password123", admin_role)

        wholesale = VendorType(name="Wholesale")
        db_session.add(wholesale)
        db_session.flush()

        active = Vendor(name="Active Co", name_normalized="active co",
                        vendor_type="Wholesale", vendor_type_id=wholesale.id)
        db_session.add(active)
        db_session.commit()

        headers = login_as(client, "admin@test.com", "password123")

        response = client.delete(
            f"/vendors/types/{wholesale.id}",
            headers=headers,
        )
        assert response.status_code == 409, response.text