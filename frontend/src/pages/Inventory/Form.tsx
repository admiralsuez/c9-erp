import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { zodResolver } from '@hookform/resolvers/zod';
import { Card, Button, Input, Textarea, Select } from '../../components/ui';
import { createItemSchema } from '../../utils/validation';
import { ArrowLeft } from 'lucide-react';
import { useCreateInventoryItem } from '../../hooks/useInventory';
import type { InventoryItemCreateRequest } from '../../api/inventory';

interface InventoryFormProps {
  isEdit?: boolean;
  itemId?: number;
}

const categories = ['Furniture', 'Supplies', 'Lighting', 'Electronics', 'Tools'];
const itemTypes = [
  { value: 'consumable', label: 'Consumable (Single-use)' },
  { value: 'returnable', label: 'Returnable (Multi-use)' },
];

export const InventoryFormPage: React.FC<InventoryFormProps> = ({ isEdit = false }) => {
  const navigate = useNavigate();
  const [submitError, setSubmitError] = useState<string | null>(null);
  const { mutate: createItem, isPending } = useCreateInventoryItem((item) => {
    navigate(`/inventory/${item.id}`);
  });

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
              <label className="block text-sm font-medium mb-2 text-neutral-700">
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
              <Select
                {...register('category_id', { valueAsNumber: true })}
                label="Category"
                placeholder="Select Category"
                error={errors.category_id?.message as string}
                disabled={isPending}
                options={categories.map((cat, idx) => ({ value: idx + 1, label: cat }))}
              />
              <Select
                {...register('item_type')}
                label="Item Type *"
                error={errors.item_type?.message as string}
                disabled={isPending}
                options={itemTypes}
              />
            </div>
          </div>
        </Card>

        {/* Section 3: Stock Management */}
        <Card padding="lg">
          <h2 className="text-lg font-semibold text-neutral-900 mb-4">
            Stock Management
          </h2>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Input
                  {...register('minimum_quantity', { valueAsNumber: true })}
                  type="number"
                  label="Minimum Quantity"
                  placeholder="e.g., 10"
                  error={errors.minimum_quantity?.message as string}
                  disabled={isPending}
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2 text-neutral-700">
                  Unit Cost
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-10 text-neutral-600">$</span>
                  <input
                    type="number"
                    step="0.01"
                    placeholder="0.00"
                    className="form-input pl-8"
                    disabled={isPending}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2 text-neutral-700">
                  Reorder Quantity
                </label>
                <input
                  type="number"
                  placeholder="e.g., 50"
                  className="form-input"
                  disabled={isPending}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2 text-neutral-700">
                  Opening Stock Quantity
                </label>
                <input
                  {...register('opening_quantity', { valueAsNumber: true })}
                  type="number"
                  placeholder="e.g., 45"
                  className="form-input"
                  disabled={isPending}
                />
                {errors.opening_quantity && (
                  <p className="form-error">{errors.opening_quantity.message as string}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium mb-2 text-neutral-700">
                  Unit of Measurement
                </label>
                <select className="form-input" disabled={isPending}>
                  <option value="units">Units</option>
                  <option value="boxes">Boxes</option>
                  <option value="kg">Kilograms</option>
                  <option value="liters">Liters</option>
                  <option value="meters">Meters</option>
                </select>
              </div>
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
                <label className="block text-sm font-medium mb-2 text-neutral-700">
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
                <label className="block text-sm font-medium mb-2 text-neutral-700">
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

        {/* Section 5: Additional Settings */}
        <Card padding="lg">
          <h2 className="text-lg font-semibold text-neutral-900 mb-4">
            Additional Settings
          </h2>
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <input
                type="checkbox"
                id="trackable"
                className="w-4 h-4 rounded border-neutral-300 text-primary-600 focus:ring-2 focus:ring-primary-500"
                disabled={isPending}
              />
              <label htmlFor="trackable" className="text-sm text-neutral-700">
                Enable tracking for this item (recommended for returnable items)
              </label>
            </div>

            <div className="flex items-center gap-4">
              <input
                type="checkbox"
                id="notify"
                className="w-4 h-4 rounded border-neutral-300 text-primary-600 focus:ring-2 focus:ring-primary-500"
                disabled={isPending}
              />
              <label htmlFor="notify" className="text-sm text-neutral-700">
                Notify me when stock falls below minimum
              </label>
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
