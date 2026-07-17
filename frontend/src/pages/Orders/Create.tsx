import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { Card, Button } from '../../components/ui';
import { formLabel } from '../../styles/classNames';
import { ArrowLeft, Trash2, Loader, Plus, Info } from 'lucide-react';
import { useCreateOrder } from '../../hooks/useOrders';
import { useVendors, useCreateVendor } from '../../hooks/useVendors';
import { useInventory } from '../../hooks/useInventory';
import { inventoryApi } from '../../api/inventory';
import type { OrderCreateRequest, OrderItemRequest } from '../../api/orders';
import type { SerialNumberResponse, InventoryItemResponse } from '../../api/inventory';

interface LocalOrderItem extends OrderItemRequest {
  id: string;
  item_name: string;
  variant_name?: string;
  serial_labels?: string[];
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
  const [selectedParentId, setSelectedParentId] = useState<number | ''>('');
  const [selectedVariantId, setSelectedVariantId] = useState<number | ''>('');
  const [selectedItemQty, setSelectedItemQty] = useState('');
  const [selectedSerialIds, setSelectedSerialIds] = useState<number[]>([]);
  const [showNewVendorForm, setShowNewVendorForm] = useState(false);
  const [newVendorName, setNewVendorName] = useState('');
  const [newVendorContact, setNewVendorContact] = useState('');
  const [newVendorPhone, setNewVendorPhone] = useState('');
  const [newVendorAddress, setNewVendorAddress] = useState('');
  const [newVendorPincode, setNewVendorPincode] = useState('');
  const [variants, setVariants] = useState<InventoryItemResponse[]>([]);
  const [serials, setSerials] = useState<SerialNumberResponse[]>([]);
  const [loadingVariants, setLoadingVariants] = useState(false);
  const [_loadingSerials, setLoadingSerials] = useState(false);

  const { mutate: createVendor, isPending: creatingVendor } = useCreateVendor((vendor) => {
    setVendorId(vendor.id);
    setShowNewVendorForm(false);
    setNewVendorName('');
    setNewVendorContact('');
    setNewVendorPhone('');
    setNewVendorAddress('');
    setNewVendorPincode('');
  });

  const { mutate: createOrder, isPending } = useCreateOrder((order) => {
    navigate(`/orders/${order.id}`);
  });
  const { data: vendorsData, isLoading: vendorsLoading } = useVendors(1, 100);
  const { data: inventoryData, isLoading: inventoryLoading } = useInventory(1, 100);

  const vendors = vendorsData?.items ?? [];
  const inventoryItems = inventoryData?.items ?? [];

  // Only show parent items (no parent_id) and standalone items in the top-level dropdown
  const parentItems = useMemo(() => {
    return inventoryItems.filter(i => !i.parent_id);
  }, [inventoryItems]);

  const selectedVendor = vendors.find((v) => v.id === vendorId);

  // When parent item changes, load its variant children
  const loadVariants = async (parentId: number) => {
    setLoadingVariants(true);
    setSelectedVariantId('');
    setSerials([]);
    setSelectedSerialIds([]);
    try {
      const parent = await inventoryApi.get(parentId);
      setVariants(parent.children || []);
    } catch {
      setVariants([]);
    }
    setLoadingVariants(false);
  };

  // When variant item changes, load its serials
  const loadSerials = async (variantId: number) => {
    setLoadingSerials(true);
    setSelectedSerialIds([]);
    try {
      const data = await inventoryApi.getSerials(variantId);
      setSerials(data.filter(s => !s.assigned_to_order_id));
    } catch {
      setSerials([]);
    }
    setLoadingSerials(false);
  };

  const resetItemSelection = () => {
    setSelectedParentId('');
    setSelectedVariantId('');
    setSelectedItemQty('');
    setSelectedSerialIds([]);
    setVariants([]);
    setSerials([]);
  };

  const toggleSerial = (sid: number) => {
    setSelectedSerialIds(prev =>
      prev.includes(sid) ? prev.filter(id => id !== sid) : [...prev, sid]
    );
  };

  const addItem = () => {
    if (!vendorId) {
      toast.error('Please select a vendor before adding items', { duration: 2000 });
      return;
    }

    const qty = parseInt(selectedItemQty, 10);
    if (!selectedItemQty || qty <= 0) {
      toast.error('Please enter a valid quantity (greater than 0)', { duration: 2000 });
      return;
    }

    // Determine the actual variant being ordered
    let actualItemId: number;
    let itemName: string;
    let variantName: string | undefined;

    if (selectedVariantId) {
      // Ordering a variant of a parent
      actualItemId = selectedVariantId as number;
      const variant = variants.find(v => v.id === actualItemId);
      if (!variant) { toast.error('Selected variant not found', { duration: 2000 }); return; }
      itemName = variant.name;
      variantName = variant.name;
    } else if (selectedParentId) {
      // Parent selected but no variant — treat parent as standalone (it has no children)
      actualItemId = selectedParentId as number;
      const parent = inventoryItems.find(i => i.id === actualItemId);
      if (!parent) { toast.error('Item not found', { duration: 2000 }); return; }
      itemName = parent.name;
    } else {
      toast.error('Please select an item', { duration: 2000 });
      return;
    }

    // Serial validation
    const hasSerials = serials.length > 0;
    if (hasSerials && selectedSerialIds.length !== qty) {
      toast.error(`Please select exactly ${qty} serial number(s) for ${itemName} (selected ${selectedSerialIds.length})`, { duration: 2000 });
      return;
    }

    // Check available quantity
    const totalOrderedForItem = items
      .filter((i) => i.item_id === actualItemId)
      .reduce((sum, i) => sum + i.quantity_ordered, 0);
    const selectedItem = variants.find(v => v.id === actualItemId) || inventoryItems.find(i => i.id === actualItemId);
    const available = selectedItem ? selectedItem.current_quantity - totalOrderedForItem : 0;

    if (qty > available) {
      toast.error(`Cannot order ${qty} units of "${itemName}" — only ${available} available`, { duration: 2000 });
      return;
    }

    const serialLabels = hasSerials
      ? serials.filter(s => selectedSerialIds.includes(s.id)).map(s => s.serial_number)
      : undefined;

    const newItem: LocalOrderItem = {
      id: `item-${Date.now()}`,
      item_id: actualItemId,
      item_name: itemName,
      variant_name: variantName,
      quantity_ordered: qty,
      serial_ids: hasSerials ? [...selectedSerialIds] : undefined,
      serial_labels: serialLabels,
    };

    setItems([...items, newItem]);
    resetItemSelection();
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
      pincode: newVendorPincode.trim() || undefined,
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

    if (!vendorId) { toast.error('Please select a vendor', { duration: 2000 }); return; }
    if (items.length === 0) { toast.error('Please add at least one item', { duration: 2000 }); return; }
    if (sameAsVendorAddress && !selectedVendor?.address?.trim()) {
      toast.error('Vendor has no address. Uncheck "Same as vendor address" or add an address to the vendor.', { duration: 3000 }); return;
    }

    if (!sameAsVendorAddress && deliveryName.trim()) {
      const phoneDigits = deliveryPhone.replace(/\D/g, '');
      if (deliveryPhone.trim() && phoneDigits.length !== 10) {
        toast.error('Delivery phone must be exactly 10 digits', { duration: 2000 }); return;
      }
      if (deliveryPincode.trim() && !/^\d{6}$/.test(deliveryPincode)) {
        toast.error('Delivery pincode must be exactly 6 digits', { duration: 2000 }); return;
      }
    }

    const orderData: OrderCreateRequest = {
      vendor_id: vendorId as number,
      items: items.map((item) => ({
        item_id: item.item_id,
        quantity_ordered: item.quantity_ordered,
        serial_ids: item.serial_ids,
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

        {/* Vendor Section */}
        <Card padding="lg">
          <h2 className="text-lg font-semibold text-neutral-900 mb-4">Vendor Information</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className={formLabel}>Select Vendor *</label>
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
                        <div>
                          <label className="block text-xs font-medium text-neutral-700 mb-1">Pincode</label>
                          <input
                            type="text"
                            value={newVendorPincode}
                            onChange={(e) => setNewVendorPincode(e.target.value)}
                            className="w-full px-2 py-1.5 text-sm border border-neutral-300 rounded"
                            placeholder="Pincode"
                          />
                        </div>
                      </div>
                      <div className="flex gap-2 justify-end">
                        <button
                          type="button"
                          onClick={() => { setShowNewVendorForm(false); setNewVendorName(''); setNewVendorContact(''); setNewVendorPhone(''); setNewVendorAddress(''); setNewVendorPincode(''); }}
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
          <div className="mb-6 pb-6 border-b border-neutral-200">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
              {/* Parent Item / Standalone Item Dropdown */}
              <div>
                <label className={formLabel}>
                  Product
                  <span className="ml-1 group relative inline-block">
                    <Info className="w-3.5 h-3.5 text-neutral-400 inline cursor-help" />
                    <span className="invisible group-hover:visible absolute left-0 top-full mt-1 w-56 p-2 bg-neutral-800 text-white text-xs rounded shadow-lg z-10">
                      Select a product. If it has variants, choose one below.
                    </span>
                  </span>
                </label>
                {inventoryLoading ? (
                  <div className="flex items-center gap-2 text-neutral-500">
                    <Loader className="w-4 h-4 animate-spin" />
                    <span>Loading...</span>
                  </div>
                ) : (
                  <select
                    value={selectedParentId}
                    onChange={(e) => {
                      const val = e.target.value ? parseInt(e.target.value) : '';
                      setSelectedParentId(val);
                      if (val) loadVariants(val);
                      else { setVariants([]); setSerials([]); setSelectedSerialIds([]); }
                      setSelectedVariantId('');
                      setSelectedItemQty('');
                    }}
                    className="w-full border border-neutral-300 rounded-lg px-3 py-2"
                  >
                    <option value="">-- Select Product --</option>
                    {parentItems.map((item) => (
                      <option key={item.id} value={item.id}>
                        {item.name} (SKU: {item.sku})
                      </option>
                    ))}
                  </select>
                )}
              </div>

              {/* Variant Dropdown (shown when parent has children) */}
              <div>
                <label className={formLabel}>
                  Variant
                  {variants.length > 0 && (
                    <span className="text-xs text-neutral-400 ml-1">({variants.length} available)</span>
                  )}
                </label>
                {loadingVariants ? (
                  <div className="flex items-center gap-2 text-neutral-500 h-10">
                    <Loader className="w-4 h-4 animate-spin" />
                  </div>
                ) : (
                  <select
                    value={selectedVariantId}
                    onChange={(e) => {
                      const val = e.target.value ? parseInt(e.target.value) : '';
                      setSelectedVariantId(val);
                      if (val) loadSerials(val);
                      else { setSerials([]); setSelectedSerialIds([]); }
                      setSelectedItemQty('');
                    }}
                    className="w-full border border-neutral-300 rounded-lg px-3 py-2"
                    disabled={!selectedParentId || variants.length === 0}
                  >
                    <option value="">
                      {!selectedParentId
                        ? '-- Select product first --'
                        : variants.length === 0
                          ? '-- No variants (standalone item) --'
                          : '-- Select variant --'}
                    </option>
                    {variants.map((v) => {
                      const totalOrdered = items.filter(i => i.item_id === v.id).reduce((s, i) => s + i.quantity_ordered, 0);
                      const available = v.current_quantity - totalOrdered;
                      const desc = v.description || '';
                      const prim = desc.match(/Primary:\s*(.*?)(?:\s*\||$)/)?.[1]?.trim() || '';
                      const sec = desc.match(/Secondary:\s*(.*?)(?:\s*\||$)/)?.[1]?.trim() || '';
                      return (
                        <option key={v.id} value={v.id}>
                          {v.name}{prim ? ` | ${prim}` : ''}{sec ? ` | ${sec}` : ''} | {Math.max(0, available)} qty
                        </option>
                      );
                    })}
                  </select>
                )}
              </div>

              {/* Quantity */}
              <div>
                <label className={formLabel}>Quantity</label>
                <input
                  type="number"
                  min="1"
                  value={selectedItemQty}
                  onChange={(e) => setSelectedItemQty(e.target.value)}
                  placeholder={serials.length > 0 ? 'Must match serial count' : 'Enter qty'}
                  className="w-full border border-neutral-300 rounded-lg px-3 py-2"
                  disabled={!selectedParentId}
                />
              </div>

              <div className="flex items-end">
                <Button
                  type="button"
                  onClick={addItem}
                  disabled={!selectedParentId || !selectedItemQty || (serials.length > 0 && selectedSerialIds.length !== parseInt(selectedItemQty || '0'))}
                  className="w-full bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50"
                >
                  Add Item
                </Button>
              </div>
            </div>

            {/* Serial Picker — shown when variant has serials */}
            {serials.length > 0 && (
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm font-medium text-blue-800 mb-2">
                  Select {selectedItemQty || '...'} serial number(s) for this variant:
                </p>
                <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto">
                  {serials.map((s) => {
                    const selected = selectedSerialIds.includes(s.id);
                    return (
                      <button
                        key={s.id}
                        type="button"
                        onClick={() => toggleSerial(s.id)}
                        className={`px-2 py-1 text-xs font-mono rounded border transition-colors ${
                          selected
                            ? 'bg-primary-600 text-white border-primary-600'
                            : 'bg-white text-neutral-700 border-neutral-300 hover:bg-neutral-100'
                        }`}
                      >
                        {s.serial_number}
                      </button>
                    );
                  })}
                </div>
                <p className="text-xs text-blue-600 mt-1">
                  Selected: {selectedSerialIds.length} / {selectedItemQty || '?'}
                </p>
              </div>
            )}
          </div>

          {/* Items List */}
          {items.length > 0 ? (
            <div className="space-y-2">
              {items.map((item) => (
                <div key={item.id} className="flex items-center justify-between p-3 bg-neutral-50 rounded-lg">
                  <div>
                    <p className="font-medium text-neutral-900">{item.item_name}</p>
                    <p className="text-sm text-neutral-600">Quantity: {item.quantity_ordered}</p>
                    {item.serial_labels && item.serial_labels.length > 0 && (
                      <p className="text-xs text-neutral-500 mt-0.5">
                        Serials: {item.serial_labels.join(', ')}
                      </p>
                    )}
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
              <label className={formLabel}>Delivery Address</label>
              <label className="flex items-center gap-2 mb-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={sameAsVendorAddress}
                  onChange={(e) => {
                    setSameAsVendorAddress(e.target.checked);
                    if (!e.target.checked) { setDeliveryName(''); setDeliveryPhone(''); setDeliveryAddressText(''); setDeliveryPincode(''); }
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
                      <input type="text" value={deliveryName} onChange={(e) => setDeliveryName(e.target.value)} placeholder="Recipient name" className="w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm" />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-neutral-700 mb-1">Phone (10 digits)</label>
                      <input type="tel" value={deliveryPhone} onChange={(e) => setDeliveryPhone(e.target.value.replace(/\D/g, '').slice(0, 10))} placeholder="9876543210" maxLength={10} className="w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm" />
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-neutral-700 mb-1">Address</label>
                    <textarea value={deliveryAddressText} onChange={(e) => setDeliveryAddressText(e.target.value)} placeholder="Street, area, landmark, city..." rows={2} className="w-full border border-neutral-300 rounded-lg px-3 py-2 text-sm" />
                  </div>
                  <div className="sm:w-1/3">
                    <label className="block text-xs font-medium text-neutral-700 mb-1">Pincode (6 digits)</label>
                    <input type="text" value={deliveryPincode} onChange={(e) => setDeliveryPincode(e.target.value.replace(/\D/g, '').slice(0, 6))} placeholder="400001" maxLength={6} className="w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm" />
                  </div>
                </div>
              )}
            </div>

            <div>
              <label className={formLabel}>Remarks</label>
              <textarea value={remarks} onChange={(e) => setRemarks(e.target.value)} placeholder="Add any special remarks or notes..." rows={3} className="w-full border border-neutral-300 rounded-lg px-3 py-2" />
            </div>
          </div>
        </Card>

        {/* Submit Section */}
        <div className="flex gap-3 justify-end">
          <Button type="button" onClick={() => navigate('/orders')} className="px-6 py-2 border border-neutral-300 rounded-lg text-neutral-700 hover:bg-neutral-50">
            Cancel
          </Button>
          <Button type="submit" disabled={isPending || items.length === 0} className="px-6 py-2 bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50 flex items-center gap-2">
            {isPending && <Loader className="w-4 h-4 animate-spin" />}
            {isPending ? 'Creating...' : 'Create Order'}
          </Button>
        </div>
      </form>
    </div>
  );
};
