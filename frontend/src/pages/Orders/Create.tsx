import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Button } from '../../components/ui';
import { cardErrorPadded, formLabel } from '../../styles/classNames';
import { ArrowLeft, Trash2, Loader, AlertCircle, Plus } from 'lucide-react';
import { useCreateOrder } from '../../hooks/useOrders';
import { useVendors, useCreateVendor } from '../../hooks/useVendors';
import { useInventory } from '../../hooks/useInventory';
import type { OrderCreateRequest } from '../../api/orders';

interface LocalOrderItem {
  id: string;
  item_id: number;
  item_name: string;
  quantity_ordered: number;
}

export const OrderCreatePage: React.FC = () => {
  const navigate = useNavigate();
  const [vendorId, setVendorId] = useState<number | ''>('');
  const [remarks, setRemarks] = useState('');
  const [sameAsVendorAddress, setSameAsVendorAddress] = useState(false);
  const [deliveryName, setDeliveryName] = useState('');
  const [deliveryPhone, setDeliveryPhone] = useState('');
  const [deliveryAddressText, setDeliveryAddressText] = useState('');
  const [deliveryPincode, setDeliveryPincode] = useState('');
  const [items, setItems] = useState<LocalOrderItem[]>([]);
  const [selectedItemId, setSelectedItemId] = useState<number | ''>('');
  const [selectedItemQty, setSelectedItemQty] = useState('');
  const [formError, setFormError] = useState('');
  const [showNewVendorForm, setShowNewVendorForm] = useState(false);
  const [newVendorName, setNewVendorName] = useState('');
  const [newVendorContact, setNewVendorContact] = useState('');
  const [newVendorPhone, setNewVendorPhone] = useState('');
  const [newVendorAddress, setNewVendorAddress] = useState('');

  const { mutate: createVendor, isPending: creatingVendor } = useCreateVendor((vendor) => {
    setVendorId(vendor.id);
    setShowNewVendorForm(false);
    setNewVendorName('');
    setNewVendorContact('');
    setNewVendorPhone('');
    setNewVendorAddress('');
  });

  const { mutate: createOrder, isPending } = useCreateOrder((order) => {
    navigate(`/orders/${order.id}`);
  });
  const { data: vendorsData, isLoading: vendorsLoading } = useVendors(1, 100);
  const { data: inventoryData, isLoading: inventoryLoading } = useInventory(1, 100);

  const vendors = vendorsData?.items ?? [];
  const inventoryItems = inventoryData?.items ?? [];
  const selectedVendor = vendors.find((v) => v.id === vendorId);

  // Auto-fill delivery address from vendor when checkbox is on or vendor changes
  React.useEffect(() => {
    if (sameAsVendorAddress && selectedVendor) {
      setDeliveryName(selectedVendor.contact_person || selectedVendor.name);
      setDeliveryPhone(selectedVendor.phone || '');
      const parts = [selectedVendor.address, selectedVendor.city, selectedVendor.state].filter(Boolean);
      setDeliveryAddressText(parts.join(', '));
    }
  }, [sameAsVendorAddress, vendorId]);

  const addItem = () => {
    setFormError('');

    if (!vendorId) {
      setFormError('Please select a vendor before adding items');
      return;
    }

    if (!selectedItemId) {
      setFormError('Please select an item');
      return;
    }

    const qty = parseInt(selectedItemQty, 10);
    if (!selectedItemQty || qty <= 0) {
      setFormError('Please enter a valid quantity (greater than 0)');
      return;
    }

    const item = inventoryItems.find((i) => i.id === selectedItemId);
    if (!item) {
      setFormError('Item not found');
      return;
    }

    // Check available quantity (hard block - don't allow over-order)
    const totalOrderedForItem = items
      .filter((i) => i.item_id === item.id)
      .reduce((sum, i) => sum + i.quantity_ordered, 0);
    const available = item.current_quantity - totalOrderedForItem;

    if (qty > available) {
      const overBy = qty - available;
      setFormError(
        `Cannot order ${qty} units of "${item.name}" — only ${available} available` +
        (overBy > 0 ? ` (exceeds by ${overBy})` : '')
      );
      return;
    }

    const newItem: LocalOrderItem = {
      id: `item-${Date.now()}`,
      item_id: item.id,
      item_name: item.name,
      quantity_ordered: qty,
    };

    setItems([...items, newItem]);
    setSelectedItemId('');
    setSelectedItemQty('');
  };

  const removeItem = (id: string) => {
    setItems(items.filter((item) => item.id !== id));
  };

  const handleCreateVendor = () => {
    if (!newVendorName.trim()) return;
    createVendor({
      name: newVendorName.trim(),
      contact_person: newVendorContact.trim() || undefined,
      phone: newVendorPhone.trim() || undefined,
      address: newVendorAddress.trim() || undefined,
    });
  };

  const buildDeliveryAddress = (): string | undefined => {
    if (sameAsVendorAddress || (!deliveryName && !deliveryAddressText)) {
      return undefined;
    }
    return [deliveryName, deliveryPhone, deliveryAddressText, deliveryPincode].filter(Boolean).join(' | ');
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');

    if (!vendorId) {
      setFormError('Please select a vendor');
      return;
    }

    if (items.length === 0) {
      setFormError('Please add at least one item to the order');
      return;
    }

    if (!sameAsVendorAddress && deliveryName.trim()) {
      const phoneDigits = deliveryPhone.replace(/\D/g, '');
      if (deliveryPhone.trim() && phoneDigits.length !== 10) {
        setFormError('Delivery phone must be exactly 10 digits');
        return;
      }
      if (deliveryPincode.trim() && !/^\d{6}$/.test(deliveryPincode)) {
        setFormError('Delivery pincode must be exactly 6 digits');
        return;
      }
    }

    const orderData: OrderCreateRequest = {
      vendor_id: vendorId as number,
      items: items.map((item) => ({
        item_id: item.item_id,
        quantity_ordered: item.quantity_ordered,
      })),
      remarks: remarks || undefined,
      delivery_address: buildDeliveryAddress(),
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
            <h1 className="text-3xl font-bold text-neutral-900">Create New Order</h1>
            <p className="text-neutral-600 mt-1">Select vendor, items, and confirm details</p>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {formError && (
          <Card className={cardErrorPadded} padding="lg">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-error flex-shrink-0" />
              <p className="text-error">{formError}</p>
            </div>
          </Card>
        )}

        {/* Vendor Section */}
        <Card padding="lg">
          <h2 className="text-lg font-semibold text-neutral-900 mb-4">Vendor Information</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className={formLabel}>
                Select Vendor *
              </label>
              {vendorsLoading ? (
                <div className="flex items-center gap-2 text-neutral-500">
                  <Loader className="w-4 h-4 animate-spin" />
                  <span>Loading vendors...</span>
                </div>
              ) : (
                <>
                <select
                  value={vendorId}
                  onChange={(e) => setVendorId(e.target.value ? parseInt(e.target.value) : '')}
                  className="form-input w-full border border-neutral-300 rounded-lg px-3 py-2"
                  required
                >
                  <option value="">-- Choose a vendor --</option>
                  {vendors.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.name}
                      {v.city && ` (${v.city})`}
                    </option>
                  ))}
                </select>
                <div className="mt-2">
                  {!showNewVendorForm ? (
                    <button
                      type="button"
                      onClick={() => setShowNewVendorForm(true)}
                      className="flex items-center gap-1 text-sm text-primary-600 hover:text-primary-700"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      New Vendor
                    </button>
                  ) : (
                    <div className="mt-3 p-3 border border-neutral-200 rounded-lg bg-neutral-50 space-y-3">
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs font-medium text-neutral-700 mb-1">Name *</label>
                          <input
                            type="text"
                            value={newVendorName}
                            onChange={(e) => setNewVendorName(e.target.value)}
                            className="w-full px-2 py-1.5 text-sm border border-neutral-300 rounded"
                            placeholder="Vendor name"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-neutral-700 mb-1">Contact</label>
                          <input
                            type="text"
                            value={newVendorContact}
                            onChange={(e) => setNewVendorContact(e.target.value)}
                            className="w-full px-2 py-1.5 text-sm border border-neutral-300 rounded"
                            placeholder="Contact person"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-neutral-700 mb-1">Phone</label>
                          <input
                            type="text"
                            value={newVendorPhone}
                            onChange={(e) => setNewVendorPhone(e.target.value)}
                            className="w-full px-2 py-1.5 text-sm border border-neutral-300 rounded"
                            placeholder="Phone"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-neutral-700 mb-1">Address</label>
                          <input
                            type="text"
                            value={newVendorAddress}
                            onChange={(e) => setNewVendorAddress(e.target.value)}
                            className="w-full px-2 py-1.5 text-sm border border-neutral-300 rounded"
                            placeholder="Address"
                          />
                        </div>
                      </div>
                      <div className="flex gap-2 justify-end">
                        <button
                          type="button"
                          onClick={() => {
                            setShowNewVendorForm(false);
                            setNewVendorName('');
                            setNewVendorContact('');
                            setNewVendorPhone('');
                            setNewVendorAddress('');
                          }}
                          className="px-3 py-1.5 text-sm border border-neutral-300 rounded text-neutral-700 hover:bg-neutral-100"
                        >
                          Cancel
                        </button>
                        <button
                          type="button"
                          onClick={handleCreateVendor}
                          disabled={creatingVendor || !newVendorName.trim()}
                          className="px-3 py-1.5 text-sm bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50 flex items-center gap-1"
                        >
                          {creatingVendor && <Loader className="w-3 h-3 animate-spin" />}
                          Create
                        </button>
                      </div>
                    </div>
                  )}
                </div>
                </>
              )}
            </div>

            {selectedVendor && (
              <div>
                <label className={formLabel}>
                  Vendor Details
                </label>
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
          <div className="mb-6 pb-6 border-b border-neutral-200">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div>
                <label className={formLabel}>Item</label>
                {inventoryLoading ? (
                  <div className="flex items-center gap-2 text-neutral-500">
                    <Loader className="w-4 h-4 animate-spin" />
                    <span>Loading items...</span>
                  </div>
                ) : (
                  <>
                    <select
                      value={selectedItemId}
                      onChange={(e) => setSelectedItemId(e.target.value ? parseInt(e.target.value) : '')}
                      className="w-full border border-neutral-300 rounded-lg px-3 py-2"
                    >
                      <option value="">-- Select Item --</option>
                      {inventoryItems.map((item) => {
                        const totalOrdered = items
                          .filter((i) => i.item_id === item.id)
                          .reduce((sum, i) => sum + i.quantity_ordered, 0);
                        const available = item.current_quantity - totalOrdered;
                        return (
                          <option key={item.id} value={item.id}>
                            {item.name} (SKU: {item.sku}) - Available: {available}/{item.current_quantity}
                          </option>
                        );
                      })}
                    </select>
                    {selectedItemId && (() => {
                      const item = inventoryItems.find((i) => i.id === selectedItemId);
                      if (!item) return null;
                      const totalOrdered = items
                        .filter((i) => i.item_id === item.id)
                        .reduce((sum, i) => sum + i.quantity_ordered, 0);
                      const available = item.current_quantity - totalOrdered;
                      return available <= 5 ? (
                        <p className="text-xs text-warning mt-1">⚠️ Low stock: only {available} available</p>
                      ) : null;
                    })()}
                  </>
                )}
              </div>

              <div>
                <label className={formLabel}>Quantity</label>
                <input
                  type="number"
                  min="1"
                  value={selectedItemQty}
                  onChange={(e) => setSelectedItemQty(e.target.value)}
                  placeholder="Enter quantity"
                  className="w-full border border-neutral-300 rounded-lg px-3 py-2"
                />
              </div>

              <div className="flex items-end">
                <Button
                  type="button"
                  onClick={addItem}
                  disabled={inventoryLoading || !selectedItemId || !selectedItemQty}
                  className="w-full bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50"
                >
                  Add Item
                </Button>
              </div>
            </div>
          </div>

          {/* Items List */}
          {items.length > 0 ? (
            <div className="space-y-2">
              {items.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between p-3 bg-neutral-50 rounded-lg"
                >
                  <div>
                    <p className="font-medium text-neutral-900">{item.item_name}</p>
                    <p className="text-sm text-neutral-600">Quantity: {item.quantity_ordered}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => removeItem(item.id)}
                    className="p-2 text-error hover:bg-error/10 rounded-lg transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-neutral-500 text-center py-4">No items added yet</p>
          )}
        </Card>

        {/* Additional Info */}
        <Card padding="lg">
          <h2 className="text-lg font-semibold text-neutral-900 mb-4">Additional Information</h2>
          <div className="space-y-4">
            <div>
              <label className={formLabel}>
                Delivery Address
              </label>
              <label className="flex items-center gap-2 mb-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={sameAsVendorAddress}
                  onChange={(e) => {
                    setSameAsVendorAddress(e.target.checked);
                    if (!e.target.checked) {
                      setDeliveryName('');
                      setDeliveryPhone('');
                      setDeliveryAddressText('');
                      setDeliveryPincode('');
                    }
                  }}
                  className="w-4 h-4 rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="text-sm text-neutral-700">Same as vendor address</span>
              </label>
              {!sameAsVendorAddress && (
                <div className="space-y-3">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-medium text-neutral-700 mb-1">Recipient Name</label>
                      <input
                        type="text"
                        value={deliveryName}
                        onChange={(e) => setDeliveryName(e.target.value)}
                        placeholder="Recipient name"
                        className="w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-neutral-700 mb-1">Phone (10 digits)</label>
                      <input
                        type="tel"
                        value={deliveryPhone}
                        onChange={(e) => setDeliveryPhone(e.target.value.replace(/\D/g, '').slice(0, 10))}
                        placeholder="9876543210"
                        maxLength={10}
                        className="w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-neutral-700 mb-1">Address</label>
                    <textarea
                      value={deliveryAddressText}
                      onChange={(e) => setDeliveryAddressText(e.target.value)}
                      placeholder="Street, area, landmark, city..."
                      rows={2}
                      className="w-full border border-neutral-300 rounded-lg px-3 py-2 text-sm"
                    />
                  </div>
                  <div className="sm:w-1/3">
                    <label className="block text-xs font-medium text-neutral-700 mb-1">Pincode (6 digits)</label>
                    <input
                      type="text"
                      value={deliveryPincode}
                      onChange={(e) => setDeliveryPincode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                      placeholder="400001"
                      maxLength={6}
                      className="w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm"
                    />
                  </div>
                </div>
              )}
            </div>

            <div>
              <label className={formLabel}>Remarks</label>
              <textarea
                value={remarks}
                onChange={(e) => setRemarks(e.target.value)}
                placeholder="Add any special remarks or notes..."
                rows={3}
                className="w-full border border-neutral-300 rounded-lg px-3 py-2"
              />
            </div>
          </div>
        </Card>

        {/* Submit Section */}
        <div className="flex gap-3 justify-end">
          <Button
            type="button"
            onClick={() => navigate('/orders')}
            className="px-6 py-2 border border-neutral-300 rounded-lg text-neutral-700 hover:bg-neutral-50"
          >
            Cancel
          </Button>
          <Button
            type="submit"
            disabled={isPending || items.length === 0}
            className="px-6 py-2 bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50 flex items-center gap-2"
          >
            {isPending && <Loader className="w-4 h-4 animate-spin" />}
            {isPending ? 'Creating...' : 'Create Order'}
          </Button>
        </div>
      </form>
    </div>
  );
};
