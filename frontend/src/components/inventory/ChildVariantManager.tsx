import React, { useState } from 'react';
import { X, Camera } from 'lucide-react';
import { Button, Card } from '../ui';
import toast from 'react-hot-toast';

interface ChildVariant {
  id: number;
  name: string;
  sku: string;
  description: string;
  image_url?: string;
  front_image_url?: string;
  back_image_url?: string;
}

interface ChildVariantManagerProps {
  variant: ChildVariant;
  onUpdate: (id: number, data: Partial<ChildVariant>) => void;
  isUpdating?: boolean;
}

export const ChildVariantManager: React.FC<ChildVariantManagerProps> = ({
  variant,
  onUpdate,
  isUpdating = false,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [primaryAttr, setPrimaryAttr] = useState('');
  const [secondaryAttr, setSecondaryAttr] = useState('');
  const [uploadingFront, setUploadingFront] = useState(false);
  const [uploadingBack, setUploadingBack] = useState(false);

  // Parse primary and secondary attributes from description
  React.useEffect(() => {
    if (variant.description) {
      const primMatch = variant.description.match(/Primary:\s*(.*?)(?:\s*\||$)/);
      const secMatch = variant.description.match(/Secondary:\s*(.*?)(?:\s*\||$)/);
      setPrimaryAttr(primMatch?.[1]?.trim() || '');
      setSecondaryAttr(secMatch?.[1]?.trim() || '');
    }
  }, [variant.description, isExpanded]);

  const handleAttributeUpdate = () => {
    const newDescription = [
      primaryAttr ? `Primary: ${primaryAttr}` : '',
      secondaryAttr ? `Secondary: ${secondaryAttr}` : '',
    ]
      .filter(Boolean)
      .join(' | ');

    onUpdate(variant.id, { description: newDescription });
    toast.success('Attributes updated');
  };

  const handleImageUpload = async (file: File, imageType: 'front' | 'back') => {
    if (imageType === 'front') {
      setUploadingFront(true);
    } else {
      setUploadingBack(true);
    }

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('image_type', imageType);

      // TODO: Call API to upload image
      // For now, create a local preview
      const reader = new FileReader();
      reader.onload = (e) => {
        const imageUrl = e.target?.result as string;
        if (imageType === 'front') {
          onUpdate(variant.id, { front_image_url: imageUrl });
        } else {
          onUpdate(variant.id, { back_image_url: imageUrl });
        }
        toast.success(`${imageType} image uploaded`);
      };
      reader.readAsDataURL(file);
    } catch (error) {
      toast.error(`Failed to upload ${imageType} image`);
    } finally {
      if (imageType === 'front') {
        setUploadingFront(false);
      } else {
        setUploadingBack(false);
      }
    }
  };

  const removeImage = (imageType: 'front' | 'back') => {
    if (imageType === 'front') {
      onUpdate(variant.id, { front_image_url: undefined });
    } else {
      onUpdate(variant.id, { back_image_url: undefined });
    }
    toast.success(`${imageType} image removed`);
  };

  return (
    <Card padding="md" className="border border-neutral-200 bg-neutral-50/50">
      <div className="flex items-center justify-between gap-3">
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-medium text-neutral-900">{variant.name}</h4>
          <p className="text-xs text-neutral-500">SKU: {variant.sku}</p>
        </div>
        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          className="px-3 py-1 text-xs font-medium text-primary-600 hover:bg-primary-50 rounded transition-colors"
        >
          {isExpanded ? 'Collapse' : 'Edit'}
        </button>
      </div>

      {isExpanded && (
        <div className="mt-4 pt-4 border-t border-neutral-200 space-y-4">
          {/* Attributes */}
          <div className="space-y-3">
            <h5 className="text-xs font-semibold text-neutral-900 uppercase tracking-wide">Attributes</h5>
            <div className="space-y-2">
              <div>
                <label className="block text-xs font-medium text-neutral-700 mb-1">
                  Primary Attribute
                </label>
                <input
                  type="text"
                  value={primaryAttr}
                  onChange={(e) => setPrimaryAttr(e.target.value)}
                  placeholder="e.g., Color: Red"
                  className="w-full px-2 py-1.5 border border-neutral-300 rounded text-sm"
                  disabled={isUpdating}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-neutral-700 mb-1">
                  Secondary Attribute (Serial Number)
                </label>
                <input
                  type="text"
                  value={secondaryAttr}
                  onChange={(e) => setSecondaryAttr(e.target.value)}
                  placeholder="e.g., Serial: SN-12345"
                  className="w-full px-2 py-1.5 border border-neutral-300 rounded text-sm"
                  disabled={isUpdating}
                />
              </div>
              <Button
                type="button"
                onClick={handleAttributeUpdate}
                disabled={isUpdating}
                className="w-full px-2 py-1.5 bg-primary-600 text-white text-xs hover:bg-primary-700 disabled:opacity-50 rounded"
              >
                Update Attributes
              </Button>
            </div>
          </div>

          {/* Images */}
          <div className="space-y-3">
            <h5 className="text-xs font-semibold text-neutral-900 uppercase tracking-wide">Images</h5>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {/* Front Image */}
              <div className="p-2 border border-neutral-300 rounded-lg">
                <p className="text-xs font-medium text-neutral-700 mb-2">Front Image</p>
                {variant.front_image_url ? (
                  <div className="relative group">
                    <img
                      src={variant.front_image_url}
                      alt="Front"
                      className="w-full h-32 object-cover rounded border border-neutral-200"
                    />
                    <button
                      type="button"
                      onClick={() => removeImage('front')}
                      className="absolute top-1 right-1 p-1 bg-error text-white rounded opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ) : (
                  <label className="block p-4 border-2 border-dashed border-neutral-300 rounded-lg hover:border-primary-400 cursor-pointer text-center">
                    <Camera className="w-4 h-4 mx-auto text-neutral-400 mb-1" />
                    <span className="text-xs text-neutral-600">Click to upload</span>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) handleImageUpload(file, 'front');
                      }}
                      disabled={uploadingFront || isUpdating}
                      className="hidden"
                    />
                  </label>
                )}
              </div>

              {/* Back Image */}
              <div className="p-2 border border-neutral-300 rounded-lg">
                <p className="text-xs font-medium text-neutral-700 mb-2">Back Image</p>
                {variant.back_image_url ? (
                  <div className="relative group">
                    <img
                      src={variant.back_image_url}
                      alt="Back"
                      className="w-full h-32 object-cover rounded border border-neutral-200"
                    />
                    <button
                      type="button"
                      onClick={() => removeImage('back')}
                      className="absolute top-1 right-1 p-1 bg-error text-white rounded opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ) : (
                  <label className="block p-4 border-2 border-dashed border-neutral-300 rounded-lg hover:border-primary-400 cursor-pointer text-center">
                    <Camera className="w-4 h-4 mx-auto text-neutral-400 mb-1" />
                    <span className="text-xs text-neutral-600">Click to upload</span>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) handleImageUpload(file, 'back');
                      }}
                      disabled={uploadingBack || isUpdating}
                      className="hidden"
                    />
                  </label>
                )}
              </div>
            </div>
          </div>

          <div className="pt-3 border-t border-neutral-200 flex gap-2">
            <Button
              type="button"
              onClick={() => setIsExpanded(false)}
              className="flex-1 px-2 py-1.5 border border-neutral-300 text-neutral-700 text-xs hover:bg-neutral-100 rounded"
            >
              Done
            </Button>
          </div>
        </div>
      )}
    </Card>
  );
};

export default ChildVariantManager;
