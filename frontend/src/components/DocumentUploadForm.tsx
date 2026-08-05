import React, { useState, useRef } from 'react';
import { FileUp } from 'lucide-react';
import toast from 'react-hot-toast';

interface DocumentUploadFormProps {
  onAdd: (file: File, category: string, notes: string) => void;
}

const DOC_CATEGORIES = [
  { value: 'requisition', label: 'Requisition' },
  { value: 'dispatch_challan', label: 'Dispatch Challan' },
  { value: 'signed_delivery_challan', label: 'Signed Delivery Challan' },
  { value: 'invoice', label: 'Invoice' },
  { value: 'other', label: 'Other' },
];

export const DocumentUploadForm: React.FC<DocumentUploadFormProps> = ({ onAdd }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedCategory, setSelectedCategory] = useState('requisition');
  const [notes, setNotes] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      // Validate file size (max 50MB)
      if (file.size > 50 * 1024 * 1024) {
        toast.error('File size must be less than 50MB');
        setSelectedFile(null);
        return;
      }
      setSelectedFile(file);
    }
  };

  const handleAdd = () => {
    if (!selectedFile) {
      toast.error('Please select a file');
      return;
    }

    onAdd(selectedFile, selectedCategory, notes);
    
    // Reset form
    setSelectedFile(null);
    setSelectedCategory('requisition');
    setNotes('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    toast.success(`${selectedFile.name} added successfully`);
  };

  return (
    <div className="bg-neutral-50 rounded-lg p-4 space-y-4">
      {/* File Input */}
      <div>
        <label className="block text-xs font-medium text-neutral-700 mb-2">
          Select Document File
        </label>
        <div className="flex items-center gap-3">
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileChange}
            accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
            className="flex-1 block text-sm text-neutral-600 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
          />
        </div>
        {selectedFile && (
          <p className="text-xs text-success mt-1">
            ✓ {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
          </p>
        )}
        <p className="text-xs text-neutral-500 mt-1">
          Supported: PDF, JPG, PNG, DOC, DOCX (max 50MB)
        </p>
      </div>

      {/* Document Category */}
      <div>
        <label className="block text-xs font-medium text-neutral-700 mb-2">
          Document Type
        </label>
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="w-full px-3 py-2 border border-neutral-300 rounded text-sm"
        >
          {DOC_CATEGORIES.map((cat) => (
            <option key={cat.value} value={cat.value}>
              {cat.label}
            </option>
          ))}
        </select>
      </div>

      {/* Notes */}
      <div>
        <label className="block text-xs font-medium text-neutral-700 mb-2">
          Notes (Optional)
        </label>
        <input
          type="text"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          className="w-full px-3 py-2 border border-neutral-300 rounded text-sm"
          placeholder="e.g., Original copy, Signed by manager, etc."
        />
      </div>

      {/* Add Button */}
      <button
        type="button"
        onClick={handleAdd}
        disabled={!selectedFile}
        className="w-full px-4 py-2 bg-primary-600 text-white rounded text-sm font-medium hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        <FileUp className="w-4 h-4" />
        Add Document
      </button>
    </div>
  );
};

export default DocumentUploadForm;
