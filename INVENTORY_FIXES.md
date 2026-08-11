# Inventory Management Fixes - Implementation Guide

## Overview
This document describes the 4 inventory management fixes implemented in the backend. All backend endpoints are ready for frontend integration.

---

## Issue 1: Quantity Changes Not Persisting via Editing ✅

### Problem
When editing an inventory item and changing `current_quantity`, the change didn't persist. The system was designed to only allow quantity changes through stock transactions, not direct editing.

### Solution
Added a dedicated endpoint to adjust quantities with full transaction tracking.

### API Endpoint

**POST /inventory/items/{item_id}/adjust-quantity**

Adjust item quantity and automatically create a transaction record for audit trail.

**Request:**
```json
{
  "quantity_change": 10,
  "reason": "Manual recount"
}
```

**Response:**
```json
{
  "id": 1,
  "name": "Item Name",
  "sku": "SKU-001",
  "current_quantity": 110,
  "reserved_quantity": 5,
  "stock_status": "active",
  "expiry_date": null,
  "allow_no_expiry": true,
  ...
}
```

**Behavior:**
- Accepts positive or negative quantity changes
- Creates `InventoryTransaction` record with type "adjustment"
- Prevents negative final quantities
- Logs action with user, reason, and amounts
- Returns updated item with new quantity

**Frontend Implementation:**
```tsx
// Instead of editing current_quantity field:
// Call this endpoint to adjust quantity
const adjustQuantity = async (itemId: number, change: number, reason: string) => {
  const response = await fetch(`/inventory/items/${itemId}/adjust-quantity`, {
    method: 'POST',
    body: JSON.stringify({ 
      quantity_change: change,
      reason: reason 
    })
  });
  return response.json();
};

// Usage:
adjustQuantity(1, 10, 'Recount after physical audit');
```

---

## Issue 2: Images Not Displaying in Inventory ✅

### Problem
Inventory item images were stored in the database but not being returned by the API, so they couldn't be displayed in the frontend.

### Solution
Updated the `GET /inventory/items/{item_id}` endpoint to eagerly load images relationship.

### API Endpoint

**GET /inventory/items/{item_id}**

Retrieve full item details including images, transactions, and serial numbers.

**Response:**
```json
{
  "id": 1,
  "name": "Fridge ABC-100",
  "sku": "SKU-001",
  "current_quantity": 100,
  "stock_status": "active",
  "images": [
    {
      "id": 1,
      "item_id": 1,
      "image_type": "front",
      "image_url": "https://example.com/images/fridge-front.jpg",
      "uploaded_by": 5,
      "uploaded_at": "2024-08-11T10:00:00Z"
    },
    {
      "id": 2,
      "item_id": 1,
      "image_type": "back",
      "image_url": "https://example.com/images/fridge-back.jpg",
      "uploaded_by": 5,
      "uploaded_at": "2024-08-11T10:01:00Z"
    }
  ],
  "transactions": [...],
  "serial_numbers": [...],
  "parent": null,
  ...
}
```

**What Changed:**
- Added `selectinload(InventoryItem.images)` to load images
- Images are now included in response
- Schema `InventoryItemDetailResponse` already had images field

**Frontend Implementation:**
```tsx
// Fetch item details
const getItemDetails = async (itemId: number) => {
  const response = await fetch(`/inventory/items/${itemId}`);
  return response.json();
};

// Display images
function ItemDetailView({ itemId }) {
  const [item, setItem] = useState(null);
  
  useEffect(() => {
    getItemDetails(itemId).then(setItem);
  }, [itemId]);
  
  if (!item) return <div>Loading...</div>;
  
  return (
    <div>
      <h1>{item.name}</h1>
      
      {/* Display images */}
      <div className="images-gallery">
        {item.images && item.images.map(image => (
          <div key={image.id} className="image-container">
            <img src={image.image_url} alt={image.image_type} />
            <p>Type: {image.image_type}</p>
          </div>
        ))}
      </div>
      
      {/* Rest of item details */}
      <p>Quantity: {item.current_quantity}</p>
      <p>Status: {item.stock_status}</p>
    </div>
  );
}
```

---

## Issues 3 & 4: Stock Status (Expired & Damaged) ✅

### Problem
No way to track expiry dates or mark items as damaged. System needed to differentiate between active, expired, and damaged stock.

### Solution
Added three new fields to `InventoryItem` model:
- `expiry_date`: Optional datetime for perishable items
- `allow_no_expiry`: Boolean flag (default=True) to allow items without expiry requirements
- `stock_status`: String field with values: "active", "expired", "damaged"

### Database Changes

New Alembic migration: `add_inventory_stock_management.py`

```sql
ALTER TABLE inventory_items ADD COLUMN expiry_date TIMESTAMP WITH TIME ZONE NULL;
ALTER TABLE inventory_items ADD COLUMN allow_no_expiry BOOLEAN DEFAULT TRUE;
ALTER TABLE inventory_items ADD COLUMN stock_status VARCHAR(50) DEFAULT 'active';
```

### API Endpoints

#### Update Stock Status

**PATCH /inventory/items/{item_id}/stock-status**

Update item's stock status and expiry information.

**Request:**
```json
{
  "stock_status": "expired"
}
```

**Response:**
```json
{
  "id": 1,
  "name": "Item Name",
  "stock_status": "expired",
  "expiry_date": "2024-08-15T00:00:00Z",
  "allow_no_expiry": false,
  ...
}
```

**Valid Status Values:**
- `"active"` - Item is in active inventory
- `"expired"` - Item has expired (past expiry_date)
- `"damaged"` - Item is damaged and not usable

#### List Items with Stock Status Filter

**GET /inventory/items?stock_status=active**

List inventory items filtered by stock status.

**Query Parameters:**
```
GET /inventory/items?stock_status=expired
GET /inventory/items?stock_status=damaged
GET /inventory/items?stock_status=active
GET /inventory/items?stock_status=active&category_id=5&low_stock=true
```

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "name": "Item 1",
      "stock_status": "expired",
      "expiry_date": "2024-07-31T00:00:00Z",
      ...
    },
    {
      "id": 2,
      "name": "Item 2",
      "stock_status": "active",
      "expiry_date": null,
      "allow_no_expiry": true,
      ...
    }
  ],
  "total": 2,
  "page": 1,
  "size": 20,
  "pages": 1
}
```

### Schema Updates

**InventoryItemUpdate** - PATCH request schema:
```python
class InventoryItemUpdate(BaseModel):
    # ... existing fields ...
    expiry_date: Optional[datetime] = None
    allow_no_expiry: Optional[bool] = None
    stock_status: Optional[str] = None  # active | expired | damaged
```

**InventoryItemResponse** - Response schema:
```python
class InventoryItemResponse(InventoryItemBase):
    # ... existing fields ...
    expiry_date: Optional[datetime] = None
    allow_no_expiry: bool = True
    stock_status: str = "active"  # active | expired | damaged
```

### Frontend Implementation

#### Display Stock Status

```tsx
interface StockStatusProps {
  status: 'active' | 'expired' | 'damaged';
  expiryDate?: string;
  allowNoExpiry?: boolean;
}

function StockStatusBadge({ status, expiryDate, allowNoExpiry }: StockStatusProps) {
  const statusConfig = {
    active: { color: 'green', label: 'Active', icon: '✓' },
    expired: { color: 'red', label: 'Expired', icon: '✕' },
    damaged: { color: 'orange', label: 'Damaged', icon: '!' }
  };
  
  const config = statusConfig[status];
  
  return (
    <div className={`badge badge-${config.color}`}>
      <span className="icon">{config.icon}</span>
      <span className="label">{config.label}</span>
      {expiryDate && !allowNoExpiry && (
        <span className="expiry"> (Expires: {formatDate(expiryDate)})</span>
      )}
    </div>
  );
}
```

#### Update Stock Status

```tsx
async function updateItemStockStatus(
  itemId: number,
  status: 'active' | 'expired' | 'damaged'
) {
  const response = await fetch(`/inventory/items/${itemId}/stock-status`, {
    method: 'PATCH',
    body: JSON.stringify({ stock_status: status })
  });
  
  if (!response.ok) throw new Error('Failed to update stock status');
  return response.json();
}

// Usage in component
const handleMarkAsExpired = async (itemId: number) => {
  const updated = await updateItemStockStatus(itemId, 'expired');
  setItem(updated);
  showNotification(`Item marked as expired`);
};

const handleMarkAsDamaged = async (itemId: number) => {
  const updated = await updateItemStockStatus(itemId, 'damaged');
  setItem(updated);
  showNotification(`Item marked as damaged`);
};
```

#### Filter by Stock Status

```tsx
interface InventoryListProps {
  selectedStatus?: 'active' | 'expired' | 'damaged' | null;
}

function InventoryList({ selectedStatus }: InventoryListProps) {
  const [items, setItems] = useState([]);
  const [page, setPage] = useState(1);
  
  useEffect(() => {
    const params = new URLSearchParams();
    params.append('page', page.toString());
    params.append('size', '20');
    
    if (selectedStatus) {
      params.append('stock_status', selectedStatus);
    }
    
    fetch(`/inventory/items?${params}`)
      .then(r => r.json())
      .then(setItems);
  }, [selectedStatus, page]);
  
  return (
    <div>
      <div className="filters">
        <button 
          onClick={() => setPage(1)}
          className={!selectedStatus ? 'active' : ''}
        >
          All Items
        </button>
        <button 
          onClick={() => setPage(1)}
          className={selectedStatus === 'active' ? 'active' : ''}
        >
          ✓ Active
        </button>
        <button 
          onClick={() => setPage(1)}
          className={selectedStatus === 'expired' ? 'active' : ''}
        >
          ✕ Expired
        </button>
        <button 
          onClick={() => setPage(1)}
          className={selectedStatus === 'damaged' ? 'active' : ''}
        >
          ! Damaged
        </button>
      </div>
      
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>SKU</th>
            <th>Quantity</th>
            <th>Status</th>
            <th>Expiry Date</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {items.items?.map(item => (
            <tr key={item.id}>
              <td>{item.name}</td>
              <td>{item.sku}</td>
              <td>{item.current_quantity}</td>
              <td>
                <StockStatusBadge 
                  status={item.stock_status}
                  expiryDate={item.expiry_date}
                  allowNoExpiry={item.allow_no_expiry}
                />
              </td>
              <td>
                {item.expiry_date && !item.allow_no_expiry
                  ? formatDate(item.expiry_date)
                  : 'No expiry'}
              </td>
              <td>
                <button onClick={() => handleMarkAsExpired(item.id)}>
                  Mark Expired
                </button>
                <button onClick={() => handleMarkAsDamaged(item.id)}>
                  Mark Damaged
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

---

## Summary of Changes

### Backend Files Modified
1. **backend/app/models.py**
   - Added 3 fields to InventoryItem class
   - expiry_date, allow_no_expiry, stock_status

2. **backend/app/schemas.py**
   - Updated InventoryItemUpdate schema
   - Updated InventoryItemResponse schema
   - InventoryItemDetailResponse inherits new fields

3. **backend/app/routers/inventory.py**
   - Updated GET /inventory/items/{item_id} to load images
   - Added POST /inventory/items/{item_id}/adjust-quantity
   - Added PATCH /inventory/items/{item_id}/stock-status
   - Updated GET /inventory/items with stock_status filter

4. **backend/alembic/versions/**
   - New migration: add_inventory_stock_management.py

### Database Changes
- 3 new columns in inventory_items table
- All fields are nullable/have defaults for backward compatibility

### Git Commit
Commit: **e55a92f** - "Implement 4 inventory management fixes"

---

## Running Database Migration

```bash
cd backend
alembic upgrade head
```

This will:
1. Add `expiry_date` column (DateTime, nullable)
2. Add `allow_no_expiry` column (Boolean, default=True)
3. Add `stock_status` column (String, default='active')

All existing items will automatically have:
- `stock_status = 'active'`
- `allow_no_expiry = True`
- `expiry_date = NULL`

---

## Frontend Checklist

- [ ] Display item images in detail view
- [ ] Show stock_status badge with appropriate styling
- [ ] Add "Adjust Quantity" button/modal
- [ ] Add "Mark as Expired" button
- [ ] Add "Mark as Damaged" button  
- [ ] Add stock_status filter in inventory list
- [ ] Display expiry date (with "No Expiry" option)
- [ ] Show transaction history in detail view
- [ ] Add validation for expiry date (must be future date)
- [ ] Show warnings for expired items

---

## Testing Scenarios

### Test 1: Adjust Quantity
1. Navigate to inventory item detail page
2. Click "Adjust Quantity" button
3. Enter quantity change: +10, reason: "Recount"
4. Verify:
   - Item quantity updates
   - Transaction appears in history
   - Total matches expected value

### Test 2: Display Images
1. Navigate to inventory item with images uploaded
2. Verify:
   - All images display correctly
   - Image types are shown (front/back)
   - Image URLs are valid

### Test 3: Mark as Expired
1. Navigate to inventory item
2. Click "Mark as Expired" button
3. Verify:
   - Stock status changes to "expired"
   - Badge displays red "Expired" status
   - Item appears in "Expired" filter

### Test 4: Mark as Damaged
1. Navigate to inventory item
2. Click "Mark as Damaged" button
3. Verify:
   - Stock status changes to "damaged"
   - Badge displays orange "Damaged" status
   - Item appears in "Damaged" filter

### Test 5: Filter by Status
1. Navigate to inventory list
2. Click "Expired" filter
3. Verify: Only expired items display
4. Click "Damaged" filter
5. Verify: Only damaged items display
6. Click "Active" filter
7. Verify: Only active items display
