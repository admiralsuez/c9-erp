# Phase 9: New ERP Features Implementation

This document outlines the 5 new features implemented in Phase 9 of the C9 ERP system.

## Feature 1: Challan Book Number

### Overview
Allows adding a challan book number to delivery documents.

### What's New
- New field `challan_book_number` on the `Document` model
- Field is optional (nullable) and applies to delivery challan documents
- Can be set when creating or uploading documents

### Database Changes
- Table: `documents`
- New column: `challan_book_number` (String, 50, nullable)

### API Changes
- **DocumentUploadRequest**: Added optional `challan_book_number` field
- **DocumentResponse**: Includes `challan_book_number` in response

### Usage
When creating or uploading a document, include the challan book number:
```json
{
  "doc_category": "delivery_challan",
  "challan_book_number": "CB-001-2024",
  "notes": "Optional notes"
}
```

### Frontend Implementation
- Add input field for challan book number in document upload form
- Display challan book number in document details view
- Show challan book number in delivery challan PDF

---

## Feature 2: Order Backdate

### Overview
Allows creating orders with a backdate (up to 30 days in the past).

### What's New
- New optional field `order_date` in `OrderCreateRequest`
- Validates that backdate is not more than 30 days in the past
- Order number is generated based on the provided/current date
- Order is created with the specified date as `created_at`

### Database Changes
None (uses existing `Order.created_at` field)

### API Changes
- **OrderCreateRequest**: Added optional `order_date` field (datetime)

### Validation Rules
- `order_date` cannot be in the future
- `order_date` cannot be more than 30 days in the past
- If `order_date` is not provided, current time is used

### Usage
Create an order with a backdate:
```json
{
  "vendor_id": 1,
  "items": [
    {"item_id": 10, "quantity_ordered": 5}
  ],
  "order_date": "2024-07-15T10:30:00Z",
  "remarks": "Backdated order",
  "delivery_address": "..."
}
```

### Impact on Order Numbers
- Order numbers are generated based on the year of `order_date`
- If backdating to previous year, order numbers will reflect that year
- Sequence counter counts all orders in the given year

### Frontend Implementation
- Add date picker to order creation form with "Backdate" option
- Show validation error if date is more than 30 days in past or in future
- Display selected backdate in order preview

---

## Feature 3: Consumable Product Return Options

### Overview
Allows capturing return reasons for consumable items when they are returned (damaged or not needed).

### What's New
- New field `return_reason` on `OrderItem` (values: "damaged", "not_needed", null)
- New field `return_status` on `OrderItem` (values: "pending", "completed", null)
- New endpoint to set return reason: `POST /orders/{order_id}/items/{order_item_id}/return-reason`

### Database Changes
- Table: `order_items`
- New columns:
  - `return_reason` (String, 50, nullable)
  - `return_status` (String, 50, nullable)

### API Changes
- **OrderItemResponse**: Added `return_reason` and `return_status` fields
- **New Endpoint**: `POST /orders/{order_id}/items/{order_item_id}/return-reason`

### Endpoint Details
**POST /orders/{order_id}/items/{order_item_id}/return-reason**

Request body:
```json
{
  "return_reason": "damaged"
}
```

Valid return_reason values:
- `"damaged"` - Item is damaged
- `"not_needed"` - Item is no longer needed
- `null` - No return reason (default)

Response returns the updated `OrderItemResponse` with `return_status` set to "pending".

### Return Workflow
1. When returning an item, call the endpoint with the return reason
2. Item's `return_reason` is set and `return_status` becomes "pending"
3. Once return is processed, `return_status` can be updated to "completed"

### Frontend Implementation
- Add dropdown for return reason when marking items as returned
- Options: "Damaged", "Not Needed"
- Display return reason in order item details
- Show return status (Pending/Completed) in order view
- Only show return reason option for consumable items

---

## Feature 4: Closed Order PDF Generation (BUG FIX)

### Overview
Fixes issue where closed orders could not generate PDF documents.

### What Was Fixed
- Closed orders can now download their requisition PDF
- No status check prevents PDF generation for closed orders
- Maintains existing signature and document caching logic

### API Impact
- **GET /orders/{order_id}/download-pdf**: Now works for closed orders
- Existing functionality remains unchanged

### How It Works
1. When downloading PDF for closed order, system checks for existing signed requisition
2. If found, returns cached PDF
3. If not found, regenerates PDF using order data and cached signatures
4. Supports all order statuses: draft, pending_requisition, approved, dispatched, delivered, and **closed**

### Frontend Implementation
- Ensure download PDF button is enabled for closed orders
- Show PDF download option in closed order details
- No additional changes needed (uses existing endpoint)

---

## Feature 5: Challan Signature Auto-Population

### Overview
Automatically includes the dispatcher's signature in delivery challan PDFs.

### What's New
- New PDF generation method: `generate_delivery_challan()` in PDFGenerator
- New endpoint: `GET /orders/{order_id}/download-challan`
- Auto-fetches dispatcher's signature from UserSignature table
- Signature is automatically included in challan PDF (no manual input needed)

### Database Changes
None (uses existing UserSignature table)

### API Changes
- **New Endpoint**: `GET /orders/{order_id}/download-challan`
  - Query parameters:
    - `include_signature` (bool, default=true): Include dispatcher signature in PDF

### Delivery Challan PDF Features
- Shows order details (order number, vendor, date)
- Shows challan book number (if available)
- Lists all dispatched items with quantities
- Shows "Dispatch Authorization" section with:
  - Prepared By field (with signature space)
  - Dispatcher Signature (auto-populated if user has signature on file)
  - Received By field (for recipient to sign)

### Signature Auto-Population Logic
1. System finds the user who dispatched the order (from OrderTimeline)
2. Checks if that user has a signature on file (from UserSignature table)
3. If signature exists, includes it in the PDF automatically
4. If no signature, shows blank signature area with line for manual signing

### How Dispatcher Signature is Set
Users can upload their signature via the signature management endpoint:
- `POST /users/me/signature` - Upload user's digital signature
- Signature is stored as base64-encoded PNG image

### Usage
**Download delivery challan with auto-signature:**
```
GET /orders/123/download-challan?include_signature=true
```

**Download challan without signature:**
```
GET /orders/123/download-challan?include_signature=false
```

### Frontend Implementation
- Add "Download Challan" button in order detail view (for dispatched/delivered/closed orders)
- Show signature preview before generating PDF
- Option to include/exclude signature in PDF
- Display challan book number in challan form
- Auto-fetch and display dispatcher's signature information

---

## Database Migration

Run the Alembic migration to add the new fields:

```bash
cd backend
alembic upgrade head
```

Migration file: `alembic/versions/add_new_fields_phase9.py`

Changes:
- Adds `challan_book_number` to `documents` table
- Adds `return_reason` to `order_items` table
- Adds `return_status` to `order_items` table

---

## Testing Checklist

### Feature 1: Challan Book Number
- [ ] Create document with challan book number
- [ ] Verify challan book number appears in DocumentResponse
- [ ] Display challan book number in delivery challan PDF

### Feature 2: Order Backdate
- [ ] Create order with backdate 7 days ago
- [ ] Verify order number reflects the backdate year
- [ ] Verify created_at timestamp matches backdate
- [ ] Try backdate 31 days ago (should fail)
- [ ] Try future date (should fail)

### Feature 3: Consumable Return Reasons
- [ ] Set return reason to "damaged" on order item
- [ ] Set return reason to "not_needed" on order item
- [ ] Verify return_status is set to "pending"
- [ ] Verify invalid reason is rejected

### Feature 4: Closed Order PDF
- [ ] Create, approve, dispatch, deliver, and close an order
- [ ] Download PDF for closed order
- [ ] Verify PDF generates without errors

### Feature 5: Challan Signature
- [ ] Upload user signature
- [ ] Dispatch an order
- [ ] Download challan with signature
- [ ] Verify signature appears in PDF
- [ ] Download challan without signature
- [ ] Verify signature does not appear

---

## API Endpoint Summary

### New Endpoints
1. **POST /orders/{order_id}/items/{order_item_id}/return-reason**
   - Set return reason for consumable item
   - Requires: `orders.manage` permission

2. **GET /orders/{order_id}/download-challan**
   - Download delivery challan PDF
   - Query: `include_signature` (bool, default=true)
   - Allowed statuses: dispatched, delivered, closed

### Modified Endpoints
1. **POST /orders**
   - Added optional `order_date` field for backdate

2. **GET /orders/{order_id}/download-pdf**
   - Now works for closed orders (bug fix)

---

## Implementation Notes

- All features maintain backward compatibility
- Existing APIs work with or without new fields
- Database columns are nullable (safe for existing data)
- New endpoints are optional (no breaking changes)
- Auto-signature feature only includes signature if user has one on file

---

## Future Enhancements

1. Add bulk return reason setting
2. Add return reason filters in order list
3. Add signature upload UI for users
4. Add challan template customization
5. Add backdate approval workflow
6. Add return analytics reports
