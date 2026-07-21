import React, { useState } from 'react';
import { Upload, X, CheckCircle2, AlertCircle } from 'lucide-react';
import { API_BASE_URL } from '../../api/client';

interface ImageUploadProps {
  itemId?: number;
  onImageUpload?: (type: 'front' | 'back', url: string) => void;
  disabled?: boolean;
}

interface UploadedImage {
  type: 'front' | 'back';
  url?: string;
  file?: File;
  uploading: boolean;
  error?: string;
}

export const ImageUpload: React.FC<ImageUploadProps> = ({
  itemId,
  onImageUpload,
  disabled = false,
}) => {
  const [images, setImages] = useState<Record<'front' | 'back', UploadedImage>>({
    front: { type: 'front', uploading: false },
    back: { type: 'back', uploading: false },
  });

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>, imageType: 'front' | 'back') => {
    e.preventDefault();
    e.stopPropagation();

    const files = Array.from(e.dataTransfer.files);
    const imageFile = files.find((file) => file.type.startsWith('image/'));

    if (imageFile) {
      handleImageSelect(imageFile, imageType);
    }
  };

  const handleImageSelect = (file: File, imageType: 'front' | 'back') => {
    // Validate file
    const validFormats = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    const maxSize = 10 * 1024 * 1024; // 10MB

    if (!validFormats.includes(file.type)) {
      setImages((prev) => ({
        ...prev,
        [imageType]: {
          ...prev[imageType],
          error: 'Invalid image format. Allowed: JPG, PNG, GIF, WebP',
        },
      }));
      return;
    }

    if (file.size > maxSize) {
      setImages((prev) => ({
        ...prev,
        [imageType]: {
          ...prev[imageType],
          error: 'File size exceeds 10MB limit',
        },
      }));
      return;
    }

    // Create preview and store file
    const reader = new FileReader();
    reader.onload = (e) => {
      setImages((prev) => ({
        ...prev,
        [imageType]: {
          ...prev[imageType],
          file,
          url: e.target?.result as string,
          error: undefined,
        },
      }));
    };
    reader.readAsDataURL(file);
  };

  const handleFileInputChange = (
    e: React.ChangeEvent<HTMLInputElement>,
    imageType: 'front' | 'back'
  ) => {
    const file = e.target.files?.[0];
    if (file) {
      handleImageSelect(file, imageType);
    }
  };

  const handleUpload = async (imageType: 'front' | 'back') => {
    const image = images[imageType];
    if (!image.file || !itemId) return;

    setImages((prev) => ({
      ...prev,
      [imageType]: { ...prev[imageType], uploading: true, error: undefined },
    }));

    try {
      const formData = new FormData();
      formData.append('file', image.file);
      formData.append('image_type', imageType);

      const response = await fetch(`${API_BASE_URL}/inventory/items/${itemId}/upload-photo?image_type=${imageType}`, {
        method: 'POST',
        body: formData,
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      const data = await response.json();
      setImages((prev) => ({
        ...prev,
        [imageType]: {
          ...prev[imageType],
          uploading: false,
          url: data.image_url,
          file: undefined,
        },
      }));

      onImageUpload?.(imageType, data.image_url);
    } catch (error) {
      setImages((prev) => ({
        ...prev,
        [imageType]: {
          ...prev[imageType],
          uploading: false,
          error: error instanceof Error ? error.message : 'Upload failed',
        },
      }));
    }
  };

  const handleDelete = async (imageType: 'front' | 'back') => {
    const image = images[imageType];
    if (!image.url || !itemId) {
      // Just clear the preview if not uploaded yet
      setImages((prev) => ({
        ...prev,
        [imageType]: { type: imageType, uploading: false },
      }));
      return;
    }

    // Extract image ID from URL or use a stored ID
    // For now, we'll need the image ID to delete
    setImages((prev) => ({
      ...prev,
      [imageType]: { type: imageType, uploading: false },
    }));
  };

  const renderImageUploadBox = (imageType: 'front' | 'back') => {
    const image = images[imageType];
    const label = imageType === 'front' ? 'Front Image' : 'Back Image';

    if (image.url && !image.file) {
      // Image already uploaded
      return (
        <div className="relative bg-gray-100 rounded-lg overflow-hidden">
          <img src={image.url} alt={label} className="w-full h-64 object-cover" />
          <div className="absolute top-2 right-2 flex gap-2">
            <label
              htmlFor={`replace-${imageType}`}
              className="bg-blue-500 hover:bg-blue-600 text-white p-2 rounded cursor-pointer transition"
              title="Replace image"
            >
              <Upload size={18} />
            </label>
            <button
              type="button"
              onClick={() => handleDelete(imageType)}
              className="bg-red-500 hover:bg-red-600 text-white p-2 rounded transition"
              title="Delete image"
            >
              <X size={18} />
            </button>
          </div>
          <div className="absolute top-2 left-2 bg-green-500 text-white px-3 py-1 rounded text-sm font-medium flex items-center gap-1">
            <CheckCircle2 size={16} />
            Uploaded
          </div>
          <input
            id={`replace-${imageType}`}
            type="file"
            accept="image/*"
            onChange={(e) => handleFileInputChange(e, imageType)}
            className="hidden"
            disabled={disabled}
          />
        </div>
      );
    }

    if (image.file) {
      // File selected but not uploaded yet
      return (
        <div className="relative bg-gray-100 rounded-lg overflow-hidden">
          <img src={image.url} alt={label} className="w-full h-64 object-cover" />
          <div className="absolute inset-0 bg-black bg-opacity-50 flex flex-col items-center justify-center gap-3">
            {image.uploading ? (
              <>
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
                <p className="text-white text-sm font-medium">Uploading...</p>
              </>
            ) : (
              <>
                <button
                  type="button"
                  onClick={() => handleUpload(imageType)}
                  className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded font-medium transition"
                  disabled={disabled || image.uploading}
                >
                  Upload
                </button>
                <button
                  type="button"
                  onClick={() => handleDelete(imageType)}
                  className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded font-medium transition"
                  disabled={disabled}
                >
                  Cancel
                </button>
              </>
            )}
          </div>
        </div>
      );
    }

    // Empty state - waiting for upload
    return (
      <div
        onDragOver={handleDragOver}
        onDrop={(e) => handleDrop(e, imageType)}
        className={`border-2 border-dashed rounded-lg p-8 text-center transition ${
          disabled
            ? 'bg-gray-50 border-gray-200 cursor-not-allowed'
            : 'bg-blue-50 border-blue-300 hover:border-blue-400 cursor-pointer'
        }`}
      >
        <input
          id={`upload-${imageType}`}
          type="file"
          accept="image/*"
          onChange={(e) => handleFileInputChange(e, imageType)}
          className="hidden"
          disabled={disabled}
        />
        <label
          htmlFor={`upload-${imageType}`}
          className={`flex flex-col items-center gap-2 ${disabled ? 'cursor-not-allowed' : 'cursor-pointer'}`}
        >
          <Upload size={32} className={disabled ? 'text-gray-400' : 'text-blue-500'} />
          <span className={`font-medium ${disabled ? 'text-gray-500' : 'text-gray-700'}`}>
            Click to upload or drag and drop
          </span>
          <span className="text-sm text-gray-500">JPG, PNG, GIF, WebP (Max 10MB)</span>
        </label>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Item Images</h3>
        <p className="text-sm text-gray-600 mb-4">
          Upload front and back images for this item. These will be displayed in the inventory.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Front Image */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Front Image</label>
          {renderImageUploadBox('front')}
          {images.front.error && (
            <div className="mt-2 flex items-center gap-2 text-red-600 text-sm">
              <AlertCircle size={16} />
              {images.front.error}
            </div>
          )}
        </div>

        {/* Back Image */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Back Image</label>
          {renderImageUploadBox('back')}
          {images.back.error && (
            <div className="mt-2 flex items-center gap-2 text-red-600 text-sm">
              <AlertCircle size={16} />
              {images.back.error}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ImageUpload;
