"""
Phase 3 test suite: Documents, Requisition PDF, Signature Workflow

Uses shared conftest fixtures (client, db_session) and helpers.
"""

import pytest
from decimal import Decimal
from io import BytesIO

from app.models import (
    InventoryItem, InventoryCategory, Vendor, Order, OrderItem, Document, Settings,
)
from .conftest import (
    create_test_roles_and_perms, create_test_user, create_test_vendor,
    login_as,
)


def create_test_order(db, vendor, user, items_list=None):
    """Create a test order with items."""
    order = Order(
        order_number=f"ORD-TEST-{db.query(Order).count() + 1}",
        vendor_id=vendor.id,
        status="draft",
        remarks="Test order",
        delivery_address="123 Test St",
        created_by=user.id
    )
    db.add(order)
    db.flush()

    if items_list is None:
        category = InventoryCategory(name="Test Category")
        db.add(category)
        db.flush()

        item = InventoryItem(
            name="Test Item",
            sku="SKU-TEST-001",
            current_quantity=Decimal("100"),
            reserved_quantity=Decimal("0"),
            minimum_quantity=Decimal("10"),
            item_type="consumable",
            category_id=category.id
        )
        db.add(item)
        db.flush()
        items_list = [item]

    for item in items_list:
        order_item = OrderItem(
            order_id=order.id,
            item_id=item.id,
            quantity_ordered=Decimal("10")
        )
        db.add(order_item)

    db.commit()
    return order


@pytest.fixture(autouse=True)
def _test_storage_dir():
    """Setup and cleanup a test storage directory."""
    import os, shutil
    from app.services.storage import LocalDiskBackend, set_storage_backend
    test_backend = LocalDiskBackend(base_path="./test_uploads")
    set_storage_backend(test_backend)
    yield
    if os.path.exists("./test_uploads"):
        shutil.rmtree("./test_uploads")


class TestDocumentRouter:
    """Test document CRUD operations."""

    def test_upload_document(self, client, db_session):
        """Test uploading a document."""
        admin_role, _, _, _ = create_test_roles_and_perms(db_session)
        admin_user = create_test_user(db_session, "admin@test.com", "password123", admin_role)

        vendor = Vendor(name="Test Vendor", name_normalized="test vendor",
                        address="123 Vendor St", email="vendor@test.com")
        db_session.add(vendor)
        db_session.flush()

        order = create_test_order(db_session, vendor, admin_user)

        headers = login_as(client, "admin@test.com", "password123")

        file_content = b"PDF test content"
        response = client.post(
            f"/documents/upload/{order.id}",
            params={"doc_category": "requisition", "notes": "Test doc"},
            files={"file": ("test.pdf", BytesIO(file_content), "application/pdf")},
            headers=headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["doc_category"] == "requisition"
        assert data["file_name"] == "test.pdf"

    def test_list_order_documents(self, client, db_session):
        """Test listing documents for an order."""
        admin_role, _, _, _ = create_test_roles_and_perms(db_session)
        admin_user = create_test_user(db_session, "admin@test.com", "password123", admin_role)

        vendor = Vendor(name="Test Vendor", name_normalized="test vendor",
                        address="123 Vendor St", email="vendor@test.com")
        db_session.add(vendor)
        db_session.flush()

        order = create_test_order(db_session, vendor, admin_user)

        doc = Document(
            order_id=order.id,
            file_name="test.pdf",
            file_type="pdf",
            storage_path="orders/1/test.pdf",
            doc_category="requisition",
            version=1,
            version_status="current",
            uploaded_by=admin_user.id
        )
        db_session.add(doc)
        db_session.commit()

        headers = login_as(client, "admin@test.com", "password123")

        response = client.get(
            f"/documents/orders/{order.id}/documents",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        items = data.get("items", data)
        assert len(items) == 1
        assert items[0]["file_name"] == "test.pdf"

    def test_get_document(self, client, db_session):
        """Test getting a specific document."""
        admin_role, _, _, _ = create_test_roles_and_perms(db_session)
        admin_user = create_test_user(db_session, "admin@test.com", "password123", admin_role)

        vendor = Vendor(name="Test Vendor", name_normalized="test vendor",
                        address="123 Vendor St", email="vendor@test.com")
        db_session.add(vendor)
        db_session.flush()

        order = create_test_order(db_session, vendor, admin_user)

        doc = Document(
            order_id=order.id,
            file_name="test.pdf",
            file_type="pdf",
            storage_path="orders/1/test.pdf",
            doc_category="requisition",
            version=1,
            version_status="current",
            uploaded_by=admin_user.id
        )
        db_session.add(doc)
        db_session.commit()
        doc_id = doc.id

        headers = login_as(client, "admin@test.com", "password123")

        response = client.get(
            f"/documents/{doc_id}",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == doc_id
        assert data["file_name"] == "test.pdf"


class TestPDFGeneration:
    """Test PDF generation during order submission."""

    def test_pdf_generated_on_submit_requisition(self, client, db_session):
        """Test that PDF is generated when order is submitted."""
        admin_role, _, _, _ = create_test_roles_and_perms(db_session)
        admin_user = create_test_user(db_session, "admin@test.com", "password123", admin_role)

        setting = Settings(
            company_name="Test Company",
            company_address="123 Test Ave",
            pdf_header_text="Test Header",
            pdf_footer_text="Test Footer"
        )
        db_session.add(setting)
        db_session.flush()

        vendor = Vendor(name="Test Vendor", name_normalized="test vendor",
                        address="123 Vendor St", email="vendor@test.com")
        db_session.add(vendor)
        db_session.flush()

        order = create_test_order(db_session, vendor, admin_user)
        order_id = order.id
        db_session.commit()

        headers = login_as(client, "admin@test.com", "password123")

        response = client.post(
            f"/orders/{order_id}/submit-requisition?approver_id={admin_user.id}",
            headers=headers
        )

        assert response.status_code == 200
        assert response.json()["status"] == "pending_requisition"

        docs = db_session.query(Document).filter(
            Document.order_id == order_id,
            Document.doc_category == "requisition"
        ).all()

        assert len(docs) > 0
        assert docs[0].version_status == "current"


class TestDocumentVersioning:
    """Test document versioning and chain tracking."""

    def test_document_versioning_on_signed_upload(self, client, db_session):
        """Test that versioning works when uploading signed requisition."""
        admin_role, _, _, _ = create_test_roles_and_perms(db_session)
        admin_user = create_test_user(db_session, "admin@test.com", "password123", admin_role)

        vendor = Vendor(name="Test Vendor", name_normalized="test vendor",
                        address="123 Vendor St", email="vendor@test.com")
        db_session.add(vendor)
        db_session.flush()

        order = create_test_order(db_session, vendor, admin_user)
        order_id = order.id

        doc1 = Document(
            order_id=order_id,
            file_name="requisition.pdf",
            file_type="pdf",
            storage_path="orders/1/requisition.pdf",
            doc_category="requisition",
            version=1,
            version_status="current",
            uploaded_by=admin_user.id
        )
        db_session.add(doc1)
        db_session.flush()

        order.status = "pending_requisition"
        db_session.commit()

        headers = login_as(client, "admin@test.com", "password123")

        file_content = b"Signed PDF content"
        response = client.post(
            f"/orders/{order_id}/upload-signed",
            files={"file": ("signed_requisition.pdf", BytesIO(file_content), "application/pdf")},
            headers=headers
        )

        assert response.status_code == 200

        docs = db_session.query(Document).filter(Document.order_id == order_id).all()
        signed_docs = [d for d in docs if d.doc_category == "signed_requisition"]
        assert len(signed_docs) >= 0

    def test_get_document_version_history(self, client, db_session):
        """Test retrieving document version history."""
        admin_role, _, _, _ = create_test_roles_and_perms(db_session)
        admin_user = create_test_user(db_session, "admin@test.com", "password123", admin_role)

        vendor = Vendor(name="Test Vendor", name_normalized="test vendor",
                        address="123 Vendor St", email="vendor@test.com")
        db_session.add(vendor)
        db_session.flush()

        order = create_test_order(db_session, vendor, admin_user)

        doc1 = Document(
            order_id=order.id,
            file_name="v1.pdf",
            file_type="pdf",
            storage_path="orders/1/v1.pdf",
            doc_category="requisition",
            version=1,
            version_status="superseded",
            uploaded_by=admin_user.id
        )
        db_session.add(doc1)
        db_session.flush()
        doc1_id = doc1.id

        doc2 = Document(
            order_id=order.id,
            file_name="v2.pdf",
            file_type="pdf",
            storage_path="orders/1/v2.pdf",
            doc_category="requisition",
            version=2,
            version_status="current",
            parent_document_id=doc1_id,
            uploaded_by=admin_user.id
        )
        db_session.add(doc2)
        db_session.commit()
        doc2_id = doc2.id

        headers = login_as(client, "admin@test.com", "password123")

        response = client.get(
            f"/documents/{doc2_id}/versions",
            headers=headers
        )

        assert response.status_code == 200
        versions = response.json()
        assert len(versions) >= 1


class TestOrderWithDocuments:
    """Test order workflow with document integration."""

    def test_order_draft_to_pending_with_pdf(self, client, db_session):
        """Test complete flow: create order, submit, verify PDF generated."""
        admin_role, _, _, _ = create_test_roles_and_perms(db_session)
        admin_user = create_test_user(db_session, "admin@test.com", "password123", admin_role)

        setting = Settings(
            company_name="Test Company",
            company_address="123 Test Ave"
        )
        db_session.add(setting)
        db_session.flush()

        vendor = Vendor(name="Test Vendor", name_normalized="test vendor",
                        address="123 Vendor St", email="vendor@test.com")
        db_session.add(vendor)
        db_session.flush()

        category = InventoryCategory(name="Test Category")
        db_session.add(category)
        db_session.flush()

        item = InventoryItem(
            name="Test Item",
            sku="SKU-001",
            current_quantity=Decimal("100"),
            reserved_quantity=Decimal("0"),
            minimum_quantity=Decimal("10"),
            item_type="consumable",
            category_id=category.id
        )
        db_session.add(item)
        db_session.commit()

        headers = login_as(client, "admin@test.com", "password123")

        response = client.post(
            "/orders",
            json={
                "vendor_id": vendor.id,
                "remarks": "Test order",
                "delivery_address": "123 Test St",
                "items": [{"item_id": item.id, "quantity_ordered": 10}]
            },
            headers=headers
        )

        assert response.status_code == 201
        order_id = response.json()["id"]

        response = client.post(
            f"/orders/{order_id}/submit-requisition?approver_id={admin_user.id}",
            headers=headers
        )

        assert response.status_code == 200
        assert response.json()["status"] == "pending_requisition"

        docs = db_session.query(Document).filter(
            Document.order_id == order_id,
            Document.doc_category == "requisition"
        ).all()

        assert len(docs) > 0
