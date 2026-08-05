import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { Card, Button } from '../../components/ui';
import { formLabel } from '../../styles/classNames';
import { ArrowLeft, Upload, Plus, Trash2, Loader } from 'lucide-react';
import { useCreateOrder } from '../../hooks/useOrders';
import { useVendors } from '../../hooks/useVendors';
import { useInventory } from '../../hooks/useInventory';
import { inventoryApi } from '../../api/inventory';
import type { OrderCreateRequest } from '../../api/orders';
import type { InventoryItemResponse } from '../../api/inventory';

interface PastOrderItem {
  id: string;
  item_id: number;
  item_name: string;
  quantity_ordered: number;
  sku?: string;
}

export const PastOrdersPage: React.FC = () => {
  const navigate = useNavigate();
  const [vendorId, setVendorId] = useState<number | ''>('');
  const [orderDate, setOrderDate] = useState('');
  const [remarks, setRemarks] = useState('');
  const [items, setItems] = useState<PastOrderItem[]>([]);
  
  // Item selection
  const [selectedItemId, setSelectedItemId] = useState<number | ''>('');
  const [selectedItemQty, setSelectedItemQty] = useState('');
  
  const { mutate: createOrder, isPending } = useCreateOrder((order) => {
    navigate(`/orders/${order.id}`);
  });
  
  const { data: vendorsData, isLoading: vendorsLoading } = useVendors(1, 100);
  const { data: inventoryData, isLoading: inventoryLoading } = useInventory(1, 100);
  
  const vendors = vendorsData?.items ?? [];
  const inventoryItems = inventoryData?.items ?? [];
  const selectedVendor = vendors.find((v) => v.id === vendorId);

  const addItem = () => {
    if (!selectedItemId) {
      toast.error('Please select an item', { duration: 2000 });
      return;
    }
    
    const qty = parseInt(selectedItemQty, 10);
    if (!selectedItemQty || qty <= 0) {
      toast.error('Please enter a valid quantity', { duration: 2000 });
      return;
    }
    
    const selectedItem = inventoryItems.find((i) => i.id === selectedItemId);
    if (!selectedItem) {
      toast.error('Item not found', { duration: 2000 });
      return;
    }
    
    const newItem: PastOrderItem = {
      id: `item-${Date.now()}`,
      item_id: selectedItem.id,
      item_name: selectedItem.name,
      sku: selectedItem.sku,
      quantity_ordered: qty,
    };
    
    setItems([...items, newItem]);
    setSelectedItemId('');
    setSelectedItemQty('');
  };

  const removeItem = (id: string) => {
    setItems(items.filter((item) => item.id !== id));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!vendorId) {
      toast.error('Please select a vendor', { duration: 2000 });
      return;
    }
    
    if (items.length === 0) {
      toast.error('Please add at least one item', { duration: 2000 });
      return;
    }
    
    if (!orderDate) {
      toast.error('Please select an order date', { duration: 2000 });
      return;
    }
    
    const orderData: OrderCreateRequest = {
      vendor_id: vendorId as number,
      items: items.map((item) => ({
        item_id: item.item_id,
        quantity_ordered: item.quantity_ordered,
      })),
      remarks: remarks ? `[PAST ORDER] Date: ${orderDate}\n${remarks}` : `[PAST ORDER] Date: ${orderDate}`,
    };
    
    createOrder(orderData);
  };

  return (
    <div className="space-y-6 pb-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/orders')}
            className="p-2 hover:bg-neutral-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-neutral-600" />
          </button>
          <div>
            <h1 className="text-3xl font-bold text-neutral-900">Add Past Order</h1>
            <p className="text-neutral-600 mt-1">Record historical orders from your vendor</p>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        
        {/* Vendor & Date Section */}
        <Card padding="lg">
          <h2 className="text-lg font-semibold text-neutral-900 mb-4">Order Information</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className={formLabel}>Vendor *</label>
              {vendorsLoading ? (
                <div className="flex items-center gap-2 text-neutral-500">
                  <Loader className="w-4 h-4 animate-spin" />
                  <span>Loading vendors...</span>
                </div>
              ) : (
                <select
                  value={vendorId}
                  onChange={(e) => setVendorId(e.target.value ? Number(e.target.value) : '')}
                  className="form-input w-full border border-neutral-300 rounded-lg px-3 py-2"
                  required
                >
                  <option value="">-- Select a vendor --</option>
                  {vendors.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.name}
                      {v.city && ` (${v.city})`}
                    </option>
                  ))}
                </select>
              )}
            </div>

            <div>
              <label className={formLabel}>Order Date *</label>
              <input
                type="date"
                value={orderDate}
                onChange={(e) => setOrderDate(e.target.value)}
                className="form-input w-full border border-neutral-300 rounded-lg px-3 py-2"
                required
              />
            </div>

            {selectedVendor && (
              <div className="md:col-span-2">
                <label className={formLabel}>Vendor Details</label>
                <div className="bg-neutral-50 rounded-lg p-4">
                  <p className="font-medium text-neutral-900">{selectedVendor.name}</p>
                  {selectedVendor.contact_person && (
                    <p className="text-sm text-neutral-600">Contact: {selectedVendor.contact_person}</p>
                  )}
                  {selectedVendor.city && (
                    <p className="text-sm text-neutral-600">{selectedVendor.city}</p>
                  )}
                </div>
              </div>
            )}
          </div>
        </Card>

        {/* Items Section */}
        <Card padding="lg">
          <h2 className="text-lg font-semibold text-neutral-900 mb-4">Order Items</h2>
          
          {/* Add Item Form */}
          <div className="bg-neutral-50 rounded-lg p-4 mb-6 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-medium text-neutral-700 mb-1">Item *</label>
                {inventoryLoading ? (
                  <div className="flex items-center gap-2 text-neutral-500 text-sm">
                    <Loader className="w-3 h-3 animate-spin" />
                    Loading...
                  </div>
                ) : (
                  <select
                    value={selectedItemId}
                    onChange={(e) => setSelectedItemId(e.target.value ? Number(e.target.value) : '')}
                    className="w-full px-3 py-2 border border-neutral-300 rounded text-sm"
                  >
                    <option value="">-- Select item --</option>
                    {inventoryItems.map((item) => (
                      <option key={item.id} value={item.id}>
                        {item.name} ({item.sku})
                      </option>
                    ))}
                  </select>
                )}
              </div>

              <div>
                <label className="block text-xs font-medium text-neutral-700 mb-1">Quantity *</label>
                <input
                  type="number"
                  min="1"
                  value={selectedItemQty}
                  onChange={(e) => setSelectedItemQty(e.target.value)}
                  className="w-full px-3 py-2 border border-neutral-300 rounded text-sm"
                  placeholder="Enter quantity"
                />
              </div>

              <div className="flex items-end">
                <button
                  type="button"
                  onClick={addItem}
                  className="w-full px-3 py-2 bg-primary-600 text-white rounded text-sm font-medium hover:bg-primary-700 flex items-center justify-center gap-1"
                >
                  <Plus className="w-4 h-4" />
                  Add Item
                </button>
              </div>
            </div>
          </div>

          {/* Items List */}
          {items.length > 0 ? (
            <div className="space-y-3">
              {items.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between bg-neutral-50 rounded-lg p-3"
                >
                  <div>
                    <p className="font-medium text-neutral-900">{item.item_name}</p>
                    <p className="text-xs text-neutral-600">
                      SKU: {item.sku || 'N/A'} | Qty: {item.quantity_ordered}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => removeItem(item.id)}
                    className="p-2 text-red-600 hover:bg-red-50 rounded"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-neutral-500">
              <Upload className="w-8 h-8 mx-auto mb-2 text-neutral-300" />
              <p>No items added yet. Add items to create the order.</p>
            </div>
          )}
        </Card>

        {/* Remarks Section */}
        <Card padding="lg">
          <h2 className="text-lg font-semibold text-neutral-900 mb-4">Additional Notes</h2>
          <div>
            <label className={formLabel}>Remarks (Optional)</label>
            <textarea
              value={remarks}
              onChange={(e) => setRemarks(e.target.value)}
              className="form-input w-full border border-neutral-300 rounded-lg px-3 py-2 min-h-24 resize-none"
              placeholder="Add any additional notes or comments about this past order..."
            />
            <p className="text-xs text-neutral-500 mt-2">
              Note: Order date will be automatically prepended to the remarks.
            </p>
          </div>
        </Card>

        {/* Actions */}
        <div className="flex gap-3 justify-end">
          <button
            type="button"
            onClick={() => navigate('/orders')}
            className="px-6 py-2 border border-neutral-300 rounded-lg hover:bg-neutral-50 font-medium text-neutral-900"
          >
            Cancel
          </button>
          <Button
            type="submit"
            disabled={isPending || items.length === 0 || !vendorId || !orderDate}
            isLoading={isPending}
            className="px-6"
          >
            Create Past Order
          </Button>
        </div>
      </form>
    </div>
  );
};

export default PastOrdersPage;
