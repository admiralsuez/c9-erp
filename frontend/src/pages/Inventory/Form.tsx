import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { zodResolver } from '@hookform/resolvers/zod';
import { Card, Button, Input, Textarea, Select } from '../../components/ui';
import { ImageUpload } from '../../components/inventory/ImageUpload';
import { SerialNumberInput } from '../../components/inventory/SerialNumberInput';
import { formLabel } from '../../styles/classNames';
import { createItemSchema } from '../../utils/validation';
import { ArrowLeft, Plus } from 'lucide-react';
import { useCreateInventoryItem } from '../../hooks/useInventory';
import type { InventoryItemCreateRequest } from '../../api/inventory';

interface InventoryFormProps {
  isEdit?: boolean;
  itemId?: number;
}

const DEFAULT_CATEGORIES = ['Furniture', 'Supplies', 'Lighting', 'Electronics', 'Tools'];
const itemTypes = [
  { value: 'consumable', label: 'Consumable (Single-use)' },
  { value: 'returnable', label: 'Returnable (Multi-use)' },
];

export const InventoryFormPage: React.FC<InventoryFormProps> = ({ isEdit = false }) => {
  const navigate = useNavigate();
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [uploadedImages, setUploadedImages] = useState<{ front?: string; back?: string }>({});
  const [generatedSerials, setGeneratedSerials] = useState<any[]>([]);
  const [categories, setCategories] = useState(DEFAULT_CATEGORIES);
  const [showAddCategory, setShowAddCategory] = useState(false);
  const [newCategory, setNewCategory] = useState('');
  const [notifyLowStock, setNotifyLowStock] = useState(false);
  const { mutate: createItem, isPending } = useCreateInventoryItem((item) => {
    navigate(`/inventory/${item.id}`);
  });

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

  const onSubmit = async (data: any) => {
    setSubmitError(null);

    const itemData: InventoryItemCreateRequest = {
      name: data.name,
      sku: data.sku,
      barcode: data.barcode || undefined,
      category_id: data.category_id || undefined,
      item_type: data.item_type,
      current_quantity: data.opening_quantity || 0,
      minimum_quantity: data.minimum_quantity,
      description: data.description || undefined,
    };

    createItem(itemData);
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
                    placeholder="Select Category"
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
            onImageUpload={(type, url) => {
              setUploadedImages((prev) => ({ ...prev, [type]: url }));
            }}
            disabled={isPending}
          />
        </Card>

        {/* Section 3: Stock Management */}
        <Card padding="lg">
          <h2 className="text-lg font-semibold text-neutral-900 mb-4">
            Stock Management
          </h2>
          <div className="space-y-6">
            {/* Available Quantity & Safety Stock */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Input
                  {...register('opening_quantity', { valueAsNumber: true })}
                  type="number"
                  label="Available Quantity *"
                  placeholder="e.g., 45"
                  error={errors.opening_quantity?.message as string}
                  disabled={isPending}
                  helperText="Initial stock level for this item"
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
                  helperText="Minimum stock level to maintain"
                />
              </div>
            </div>

            {/* Notification Checkbox */}
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
            disabled={isPending}
          >
            {isPending ? 'Saving...' : isEdit ? 'Update Item' : 'Create Item'}
          </Button>
        </div>
      </form>
    </div>
  );
};

export default InventoryFormPage;
