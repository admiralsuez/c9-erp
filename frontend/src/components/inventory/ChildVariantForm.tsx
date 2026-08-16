import React from 'react';
import { Plus, Trash2 } from 'lucide-react';

export interface ChildFormData {
  name: string;
  sku: string;
  barcode?: string;
  item_type: 'consumable' | 'returnable';
  current_quantity: number;
  minimum_quantity: number;
  primary_attribute?: string;
  secondary_attribute?: string;
  notes?: string;
  description?: string;
  frontFile?: File;
  backFile?: File;
  frontPreview?: string;
  backPreview?: string;
}

interface ChildVariantFormProps {
  child: ChildFormData;
  index: number;
  onChange: (field: keyof ChildFormData, value: any) => void;
  onImageSelect: (imageType: 'front' | 'back', file: File) => void;
  onRemoveImage: (imageType: 'front' | 'back') => void;
  onDuplicate?: () => void;
  onRemove?: () => void;
  disabled?: boolean;
  showPhotos?: boolean;
  showRemoveButton?: boolean;
  showDuplicateButton?: boolean;
}

export const ChildVariantForm: React.FC<ChildVariantFormProps> = ({
  child,
  index,
  onChange,
  onImageSelect,
  onRemoveImage,
  onDuplicate,
  onRemove,
  disabled = false,
  showPhotos = true,
  showRemoveButton = true,
  showDuplicateButton = true,
}) => {
  return (
    <div className="border border-neutral-200 rounded-lg p-3 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-neutral-500 uppercase">Child {index + 1}</span>
        <div className="flex items-center gap-2">
          {showDuplicateButton && onDuplicate && (
            <button
              type="button"
              onClick={onDuplicate}
              className="text-primary-600 hover:text-primary-800 transition text-xs font-medium"
              title="Duplicate child"
              disabled={disabled}
            >
              + Duplicate
            </button>
          )}
          {showRemoveButton && onRemove && (
            <button
              type="button"
              onClick={onRemove}
              className="text-red-500 hover:text-red-700 transition disabled:opacity-50"
              title="Remove child"
              disabled={disabled}
            >
              <Trash2 size={16} />
            </button>
          )}
        </div>
      </div>

      {/* Name & SKU */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div>
          <label className="text-xs font-medium text-neutral-700 block mb-1">Name *</label>
          <input
            type="text"
            value={child.name}
            onChange={(e) => onChange('name', e.target.value)}
            placeholder="e.g., Visicooler-360L"
            className="form-input text-sm w-full"
            disabled={disabled}
          />
        </div>
        <div>
          <label className="text-xs font-medium text-neutral-700 block mb-1">SKU *</label>
          <input
            type="text"
            value={child.sku}
            onChange={(e) => {
              const value = e.target.value.replace(/ +/g, '-');
              onChange('sku', value);
            }}
            onKeyUp={(e) => {
              const input = e.target as HTMLInputElement;
              if (input.value.includes(' ')) {
                input.value = input.value.replace(/ +/g, '-');
              }
            }}
            placeholder="e.g., VC-360L"
            className="form-input text-sm w-full"
            disabled={disabled}
          />
        </div>
      </div>

      {/* Barcode */}
      <div>
        <label className="text-xs font-medium text-neutral-700 block mb-1">Barcode (Optional)</label>
        <input
          type="text"
          value={child.barcode || ''}
          onChange={(e) => onChange('barcode', e.target.value)}
          placeholder="e.g., 1234567890"
          className="form-input text-sm w-full"
          disabled={disabled}
        />
      </div>

      {/* Primary & Secondary Attributes */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div>
          <label className="text-xs font-medium text-neutral-700 block mb-1">Primary Attribute</label>
          <input
            type="text"
            value={child.primary_attribute || ''}
            onChange={(e) => onChange('primary_attribute', e.target.value)}
            placeholder="e.g., Capacity"
            className="form-input text-sm w-full"
            disabled={disabled}
          />
        </div>
        <div>
          <label className="text-xs font-medium text-neutral-700 block mb-1">Secondary Attribute</label>
          <input
            type="text"
            value={child.secondary_attribute || ''}
            onChange={(e) => onChange('secondary_attribute', e.target.value)}
            placeholder="e.g., 360 Liters"
            className="form-input text-sm w-full"
            disabled={disabled}
          />
        </div>
      </div>

      {/* Item Type */}
      <div>
        <label className="text-xs font-medium text-neutral-700 block mb-1">Item Type</label>
        <select
          value={child.item_type}
          onChange={(e) => onChange('item_type', e.target.value as 'consumable' | 'returnable')}
          className="form-input text-sm w-full"
          disabled={disabled}
        >
          <option value="consumable">Consumable (Single-use)</option>
          <option value="returnable">Returnable (Multi-use)</option>
        </select>
      </div>

      {/* Quantity & Min Stock */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div>
          <label className="text-xs font-medium text-neutral-700 block mb-1">Quantity</label>
          <input
            type="number"
            value={child.current_quantity}
            onChange={(e) => onChange('current_quantity', Number(e.target.value) || 0)}
            placeholder="0"
            className="form-input text-sm w-full"
            disabled={disabled}
          />
        </div>
        <div>
          <label className="text-xs font-medium text-neutral-700 block mb-1">Min. Stock</label>
          <input
            type="number"
            value={child.minimum_quantity}
            onChange={(e) => onChange('minimum_quantity', Number(e.target.value) || 0)}
            placeholder="0"
            className="form-input text-sm w-full"
            disabled={disabled}
          />
        </div>
      </div>

      {/* Notes */}
      <div>
        <label className="text-xs font-medium text-neutral-700 block mb-1">Notes (visible during ordering)</label>
        <textarea
          value={child.notes || ''}
          onChange={(e) => onChange('notes', e.target.value)}
          placeholder="e.g., Special event use only, requires manager approval"
          rows={2}
          className="form-input text-sm resize-none w-full"
          disabled={disabled}
        />
      </div>

      {/* Photos */}
      {showPhotos && (
        <div className="border border-neutral-200 rounded-lg p-3 space-y-3">
          <h5 className="text-xs font-semibold text-neutral-900 uppercase tracking-wide">Item Photos</h5>
          <p className="text-xs text-neutral-500">
            Upload front and back photos. They will be added when you save the item.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {/* Front Photo */}
            <div className="space-y-2">
              <label className="block text-xs font-medium text-neutral-700">Front Photo</label>
              {child.frontPreview ? (
                <div className="relative group">
                  <img
                    src={child.frontPreview}
                    alt="Front preview"
                    className="w-full h-32 object-cover rounded border border-neutral-200"
                  />
                  <button
                    type="button"
                    onClick={() => onRemoveImage('front')}
                    className="absolute top-1 right-1 p-1 bg-red-500 hover:bg-red-600 text-white rounded opacity-0 group-hover:opacity-100 transition-opacity text-xs"
                    title="Remove photo"
                    disabled={disabled}
                  >
                    ✕
                  </button>
                </div>
              ) : (
                <label className="block p-3 border-2 border-dashed border-neutral-300 rounded-lg hover:border-blue-400 hover:bg-blue-50 cursor-pointer text-center transition-colors disabled:opacity-50">
                  <span className="text-xs text-neutral-600 block">Click to upload</span>
                  <span className="text-xs text-neutral-500 block mt-1">JPG, PNG (Max 10MB)</span>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) onImageSelect('front', file);
                    }}
                    className="hidden"
                    disabled={disabled}
                  />
                </label>
              )}
            </div>

            {/* Back Photo */}
            <div className="space-y-2">
              <label className="block text-xs font-medium text-neutral-700">Back Photo</label>
              {child.backPreview ? (
                <div className="relative group">
                  <img
                    src={child.backPreview}
                    alt="Back preview"
                    className="w-full h-32 object-cover rounded border border-neutral-200"
                  />
                  <button
                    type="button"
                    onClick={() => onRemoveImage('back')}
                    className="absolute top-1 right-1 p-1 bg-red-500 hover:bg-red-600 text-white rounded opacity-0 group-hover:opacity-100 transition-opacity text-xs"
                    title="Remove photo"
                    disabled={disabled}
                  >
                    ✕
                  </button>
                </div>
              ) : (
                <label className="block p-3 border-2 border-dashed border-neutral-300 rounded-lg hover:border-blue-400 hover:bg-blue-50 cursor-pointer text-center transition-colors disabled:opacity-50">
                  <span className="text-xs text-neutral-600 block">Click to upload</span>
                  <span className="text-xs text-neutral-500 block mt-1">JPG, PNG (Max 10MB)</span>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) onImageSelect('back', file);
                    }}
                    className="hidden"
                    disabled={disabled}
                  />
                </label>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
