import React, { useState, useEffect, useRef } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { zodResolver } from '@hookform/resolvers/zod';
import { Card, Button, Input, Textarea, Select } from '../../components/ui';
import { ImageUpload } from '../../components/inventory/ImageUpload';
import { formLabel } from '../../styles/classNames';
import { createItemSchema } from '../../utils/validation';
import { ArrowLeft, Plus, Trash2, Info } from 'lucide-react';
import { useCreateInventoryItem, useCreateInventoryItemBatch, useInventory } from '../../hooks/useInventory';
import type { InventoryItemCreateRequest, InventoryItemChildRequest } from '../../api/inventory';

interface InventoryFormProps {
  isEdit?: boolean;
  itemId?: number;
}

const DEFAULT_CATEGORIES = ['Furniture', 'Supplies', 'Lighting', 'Electronics', 'Tools'];
const itemTypes = [
  { value: 'consumable', label: 'Consumable (Single-use)' },
  { value: 'returnable', label: 'Returnable (Multi-use)' },
];

export const InventoryFormPage: React.FC<InventoryFormProps> = ({ isEdit = false, itemId }) => {
  const navigate = useNavigate();
  const [submitError, setSubmitError] = useState<string | null>(null);

  const [categories, setCategories] = useState(DEFAULT_CATEGORIES);
  const [showAddCategory, setShowAddCategory] = useState(false);
  const [newCategory, setNewCategory] = useState('');
  const [notifyLowStock, setNotifyLowStock] = useState(false);
  const [selectedParentId, setSelectedParentId] = useState<number | ''>('');
  const [parentItems, setParentItems] = useState<Array<{ id: number; name: string; sku: string }>>([]);
  const [isParent, setIsParent] = useState(false);
  const [children, setChildren] = useState<InventoryItemChildRequest[]>([]);
  const childrenEndRef = useRef<HTMLDivElement>(null);
  const { data: itemsData } = useInventory(1, 100);
  const { mutate: createItem, isPending } = useCreateInventoryItem((item) => {
    navigate(`/inventory/${item.id}`);
  });
  const { mutate: createBatch, isPending: isBatchPending } = useCreateInventoryItemBatch((item) => {
    navigate(`/inventory/${item.id}`);
  });

  useEffect(() => {
    if (itemsData?.items) {
      setParentItems(itemsData.items.filter(i => !i.parent_id));
    }
  }, [itemsData]);

  const handleAddCategory = () => {
    if (newCategory.trim() && !categories.includes(newCategory)) {
      setCategories([...categories, newCategory]);
      setNewCategory('');
      setShowAddCategory(false);
    }
  };

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(createItemSchema),
    defaultValues: {
      name: '',
      sku: '',
      barcode: '',
      category_id: 0,
      item_type: 'consumable',
      minimum_quantity: 0,
      opening_quantity: 0,
      description: '',
    },
  });

  const addChild = () => {
    setChildren([...children, {
      name: '',
      sku: '',
      item_type: 'consumable',
      current_quantity: 0,
      minimum_quantity: 0,
      primary_attribute: '',
      secondary_attribute: '',
      notes: '',
    }]);
  };

  const removeChild = (index: number) => {
    setChildren(children.filter((_, i) => i !== index));
  };

  const duplicateChild = (index: number) => {
    const child = children[index];
    setChildren([...children, { ...child }]);
    setTimeout(() => childrenEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 0);
  };

  const updateChild = (index: number, field: keyof InventoryItemChildRequest, value: any) => {
    const updated = children.map((c, i) => i === index ? { ...c, [field]: value } : c);
    setChildren(updated);
  };

  const onSubmit = async (data: any) => {
    setSubmitError(null);

    if (isParent) {
      if (children.length === 0) {
        setSubmitError('Add at least one child item');
        return;
      }
      const invalidChildren = children.filter(c => !c.name.trim() || !c.sku.trim());
      if (invalidChildren.length > 0) {
        setSubmitError('Each child needs a name and SKU');
        return;
      }
      createBatch({
        parent: {
          name: data.name,
          sku: data.sku,
          barcode: data.barcode || undefined,
          category_id: data.category_id || undefined,
          item_type: data.item_type,
          current_quantity: 0,
          minimum_quantity: 0,
          description: data.description || undefined,
        },
        children: children.map(c => ({
          ...c,
          current_quantity: c.current_quantity || 0,
          minimum_quantity: c.minimum_quantity || 0,
        })),
      });
    } else {
      const itemData: InventoryItemCreateRequest = {
        name: data.name,
        sku: data.sku,
        barcode: data.barcode || undefined,
        category_id: data.category_id || undefined,
        item_type: data.item_type,
        current_quantity: data.opening_quantity || 0,
        minimum_quantity: data.minimum_quantity,
        description: data.description || undefined,
        parent_id: selectedParentId || undefined,
      };

      createItem(itemData);
    }
  };

  return (
    <div className="space-y-6 pb-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/inventory')}
          className="p-2 hover:bg-neutral-100 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5 text-neutral-700" />
        </button>
        <div>
          <h1 className="text-3xl font-bold text-neutral-900">
            {isEdit ? 'Edit Item' : 'Add New Item'}
          </h1>
          <p className="text-neutral-600 mt-1">
            {isEdit
              ? 'Update item details and inventory settings'
              : isParent
                ? 'Create a parent item and add multiple child variants'
                : 'Create a new inventory item with all required details'}
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Error Banner */}
        {submitError && (
          <div className="p-4 bg-error/10 border border-error rounded-lg text-sm text-error">
            {submitError}
          </div>
        )}

        {/* Parent with Children Toggle — top of form */}
        <div className="flex items-start gap-3 p-4 bg-primary-50 rounded-lg border border-primary-200">
          <input
            type="checkbox"
            id="is_parent"
            checked={isParent}
            onChange={(e) => setIsParent(e.target.checked)}
            className="w-4 h-4 rounded border-neutral-300 text-primary-600 focus:ring-2 focus:ring-primary-500 mt-1 flex-shrink-0"
            disabled={isPending || isBatchPending}
          />
          <label htmlFor="is_parent" className="text-sm text-neutral-700 flex-1 cursor-pointer">
            <span className="font-medium block mb-1">This is a parent item with variants</span>
            <span className="text-neutral-600">Create this as a parent SKU and add multiple child variants (e.g., different sizes, colors) in one go</span>
          </label>
        </div>

        {/* Section 1: Item Identity */}
        <Card padding="lg">
          <h2 className="text-lg font-semibold text-neutral-900 mb-4">
            Item Identity
          </h2>
          <div className="space-y-4">
            <div>
              <Input
                {...register('name')}
                label="Item Name"
                placeholder="e.g., Office Chair"
                error={errors.name?.message as string}
                disabled={isPending}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Input
                  {...register('sku')}
                  label="SKU (Stock Keeping Unit)"
                  placeholder="e.g., OFC-001"
                  error={errors.sku?.message as string}
                  disabled={isPending}
                />
              </div>
              <div>
                <Input
                  {...register('barcode')}
                  label="Barcode (Optional)"
                  placeholder="e.g., 1234567890"
                  error={errors.barcode?.message as string}
                  disabled={isPending}
                />
              </div>
            </div>

            <div>
              <label className={formLabel}>
                Description
              </label>
              <Textarea
                {...register('description')}
                placeholder="Detailed description of the item..."
                disabled={isPending}
              />
            </div>
          </div>
        </Card>

        {/* Section 2: Classification */}
        <Card padding="lg">
          <h2 className="text-lg font-semibold text-neutral-900 mb-4">
            Classification
          </h2>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className={formLabel}>Category</label>
                <div className="flex gap-2">
                    <select
                    {...register('category_id', { valueAsNumber: true })}
                    disabled={isPending || showAddCategory}
                    className="flex-1 form-input"
                  >
                    <option value="0">Select Category</option>
                    {categories.map((cat, idx) => (
                      <option key={idx} value={idx + 1}>
                        {cat}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    onClick={() => setShowAddCategory(!showAddCategory)}
                    className="px-3 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition disabled:bg-gray-400"
                    disabled={isPending}
                    title="Add new category"
                  >
                    <Plus size={18} />
                  </button>
                </div>
                {errors.category_id && (
                  <p className="form-error mt-1">{errors.category_id.message as string}</p>
                )}
              </div>

              <Select
                {...register('item_type')}
                label="Item Type *"
                error={errors.item_type?.message as string}
                disabled={isPending}
                options={itemTypes}
              />
            </div>
            <div className="relative">
              <label className={formLabel}>
                Parent Item (optional)
                <span className="ml-1 group inline-block">
                  <Info className="w-3.5 h-3.5 text-neutral-400 inline cursor-help" />
                  <span className="invisible group-hover:visible absolute left-0 top-full mt-1 w-64 p-2 bg-neutral-800 text-white text-xs rounded shadow-lg z-10">
                    Variants grouped under a parent share the same product family. Only parent items appear in the order form — select a variant after picking the parent.
                  </span>
                </span>
              </label>
              <select
                value={isParent ? -1 : selectedParentId}
                onChange={(e) => {
                  const val = e.target.value;
                  setSelectedParentId(val ? parseInt(val) : '');
                }}
                className="form-input"
                disabled={isPending || isParent}
              >
                <option value="">Standalone item (no parent)</option>
                {isParent && (
                  <option value="-1">This item is a parent</option>
                )}
                {parentItems
                  .filter(p => p.id !== (isEdit ? itemId : undefined))
                  .map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.sku})
                    </option>
                  ))}
              </select>
            </div>

            {/* Children Section */}
            {isParent && (
              <div className="space-y-3 border border-neutral-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-neutral-900">Child Variants</h3>
                  <button
                    type="button"
                    onClick={addChild}
                    className="text-sm px-3 py-1.5 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition flex items-center gap-1"
                    disabled={isBatchPending}
                  >
                    <Plus size={14} /> Add Child
                  </button>
                </div>

                {children.length === 0 && (
                  <p className="text-sm text-neutral-500 py-2">No children added yet. Click "Add Child" to create variants.</p>
                )}

                {children.map((child, idx) => (
                  <div key={idx} ref={idx === children.length - 1 ? childrenEndRef : undefined} className="border border-neutral-200 rounded-lg p-3 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-neutral-500 uppercase">Child {idx + 1}</span>
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => duplicateChild(idx)}
                          className="text-primary-600 hover:text-primary-800 transition text-xs font-medium"
                          title="Duplicate child"
                        >
                          + Duplicate
                        </button>
                        <button
                          type="button"
                          onClick={() => removeChild(idx)}
                          className="text-red-500 hover:text-red-700 transition"
                          title="Remove child"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div>
                        <label className="text-xs font-medium text-neutral-700 block mb-1">Name *</label>
                        <input
                          type="text"
                          value={child.name}
                          onChange={(e) => updateChild(idx, 'name', e.target.value)}
                          placeholder="e.g., Visicooler-360L"
                          className="form-input text-sm"
                          disabled={isBatchPending}
                        />
                      </div>
                      <div>
                        <label className="text-xs font-medium text-neutral-700 block mb-1">SKU *</label>
                        <input
                          type="text"
                          value={child.sku}
                          onChange={(e) => updateChild(idx, 'sku', e.target.value)}
                          placeholder="e.g., VC-360L"
                          className="form-input text-sm"
                          disabled={isBatchPending}
                        />
                      </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div>
                        <label className="text-xs font-medium text-neutral-700 block mb-1">Primary Attribute</label>
                        <input
                          type="text"
                          value={child.primary_attribute || ''}
                          onChange={(e) => updateChild(idx, 'primary_attribute', e.target.value)}
                          placeholder="e.g., Capacity"
                          className="form-input text-sm"
                          disabled={isBatchPending}
                        />
                      </div>
                      <div>
                        <label className="text-xs font-medium text-neutral-700 block mb-1">Secondary Attribute</label>
                        <input
                          type="text"
                          value={child.secondary_attribute || ''}
                          onChange={(e) => updateChild(idx, 'secondary_attribute', e.target.value)}
                          placeholder="e.g., 360 Liters"
                          className="form-input text-sm"
                          disabled={isBatchPending}
                        />
                      </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div>
                        <label className="text-xs font-medium text-neutral-700 block mb-1">Quantity</label>
                        <input
                          type="number"
                          value={child.current_quantity}
                          onChange={(e) => updateChild(idx, 'current_quantity', Number(e.target.value) || 0)}
                          placeholder="0"
                          className="form-input text-sm"
                          disabled={isBatchPending}
                        />
                      </div>
                      <div>
                        <label className="text-xs font-medium text-neutral-700 block mb-1">Min. Stock</label>
                        <input
                          type="number"
                          value={child.minimum_quantity}
                          onChange={(e) => updateChild(idx, 'minimum_quantity', Number(e.target.value) || 0)}
                          placeholder="0"
                          className="form-input text-sm"
                          disabled={isBatchPending}
                        />
                      </div>
                    </div>
                    <div>
                      <label className="text-xs font-medium text-neutral-700 block mb-1">Notes (visible during ordering)</label>
                      <textarea
                        value={child.notes || ''}
                        onChange={(e) => updateChild(idx, 'notes', e.target.value)}
                        placeholder="e.g., Special event use only, requires manager approval"
                        rows={2}
                        className="form-input text-sm resize-none"
                        disabled={isBatchPending}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Add Category Modal */}
            {showAddCategory && (
              <div className="p-4 bg-primary-50 border-2 border-primary-200 rounded-lg space-y-3">
                <div>
                  <label className="text-sm font-medium text-gray-700 block mb-2">
                    New Category Name
                  </label>
                  <input
                    type="text"
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                    placeholder="e.g., Office Equipment"
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        handleAddCategory();
                      }
                    }}
                    className="w-full form-input"
                    disabled={isPending}
                    autoFocus
                  />
                </div>
                <div className="flex gap-2 justify-end">
                  <button
                    type="button"
                    onClick={() => {
                      setShowAddCategory(false);
                      setNewCategory('');
                    }}
                    className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition"
                    disabled={isPending}
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={handleAddCategory}
                    className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition disabled:bg-gray-400 flex items-center gap-2"
                    disabled={isPending || !newCategory.trim()}
                  >
                    <Plus size={16} />
                    Add Category
                  </button>
                </div>
              </div>
            )}
          </div>
        </Card>

        {/* Section 2.5: Item Images */}
        <Card padding="lg">
          <ImageUpload
            disabled={isPending}
          />
        </Card>

        {/* Section 3: Stock Management */}
        {!isParent && (
          <Card padding="lg">
            <h2 className="text-lg font-semibold text-neutral-900 mb-4">
              Stock Management
            </h2>
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Input
                    {...register('opening_quantity', { valueAsNumber: true })}
                    type="number"
                    label="Available Quantity *"
                    placeholder="e.g., 45"
                    error={errors.opening_quantity?.message as string}
                    disabled={isPending}
                    hint="Initial stock level for this item"
                  />
                </div>
                <div>
                  <Input
                    {...register('minimum_quantity', { valueAsNumber: true })}
                    type="number"
                    label="Safety Stock *"
                    placeholder="e.g., 10"
                    error={errors.minimum_quantity?.message as string}
                    disabled={isPending}
                    hint="Minimum stock level to maintain"
                  />
                </div>
              </div>
              <div className="flex items-start gap-3 p-4 bg-neutral-50 rounded-lg border border-neutral-200">
                <input
                  type="checkbox"
                  id="notify_low_stock"
                  checked={notifyLowStock}
                  onChange={(e) => setNotifyLowStock(e.target.checked)}
                  className="w-4 h-4 rounded border-neutral-300 text-primary-600 focus:ring-2 focus:ring-primary-500 mt-1 flex-shrink-0"
                  disabled={isPending}
                />
                <label htmlFor="notify_low_stock" className="text-sm text-neutral-700 flex-1">
                  <span className="font-medium block mb-1">Notify me when stock falls below safety stock</span>
                  <span className="text-neutral-600">Receive alerts when inventory reaches the safety stock level</span>
                </label>
              </div>
            </div>
          </Card>
        )}

        {/* Section 4: Location & Supplier */}
        <Card padding="lg">
          <h2 className="text-lg font-semibold text-neutral-900 mb-4">
            Location & Supplier
          </h2>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className={formLabel}>
                  Warehouse Location
                </label>
                <input
                  type="text"
                  placeholder="e.g., Zone A - Shelf 3"
                  className="form-input"
                  disabled={isPending}
                />
              </div>

              <div>
                <label className={formLabel}>
                  Primary Supplier
                </label>
                <select className="form-input" disabled={isPending}>
                  <option value="">Select Supplier</option>
                  <option value="abc">ABC Office Supplies</option>
                  <option value="xyz">XYZ Distributors</option>
                  <option value="general">General Wholesale</option>
                </select>
              </div>
            </div>
          </div>
        </Card>

        {/* Section 5: Serial Number Tracking (Optional - After Item Creation) */}
        <Card padding="lg" className="border-2 border-dashed border-neutral-300">
          <div className="space-y-4">
            <div>
              <h2 className="text-lg font-semibold text-neutral-900 mb-2">
                Serial Number Tracking (Optional)
              </h2>
              <p className="text-sm text-neutral-600">
                Add or generate serial numbers for this item after creation. You can:
              </p>
              <ul className="text-sm text-neutral-600 list-disc list-inside mt-2 space-y-1">
                <li>Generate new serial numbers (single units or ranges like SN1000-SN1099)</li>
                <li>Add existing serial numbers that products already have</li>
              </ul>
            </div>
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
              <strong>Tip:</strong> Create the item first, then manage serial numbers from the item detail page
            </div>
          </div>
        </Card>

        {/* Action Buttons */}
        <div className="flex gap-3 sticky bottom-0 bg-neutral-50 p-4 -mx-4 border-t border-neutral-200">
          <Button
            type="button"
            onClick={() => navigate('/inventory')}
            className="flex-1 bg-neutral-200 text-neutral-900 hover:bg-neutral-300"
            disabled={isPending}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            className="flex-1 bg-primary-600 text-white hover:bg-primary-700 flex items-center justify-center gap-2"
            disabled={isPending || isBatchPending}
          >
            {isPending || isBatchPending ? 'Saving...' : isEdit ? 'Update Item' : isParent ? 'Create Parent with Children' : 'Create Item'}
          </Button>
        </div>
      </form>
    </div>
  );
};

export default InventoryFormPage;
