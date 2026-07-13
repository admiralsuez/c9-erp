import React, { useState } from 'react';
import { Upload, AlertCircle, CheckCircle2, X } from 'lucide-react';

interface SerialNumberImportProps {
  itemId: number;
  onSerialsImported?: (serials: string[]) => void;
  disabled?: boolean;
}

export const SerialNumberImport: React.FC<SerialNumberImportProps> = ({
  itemId,
  onSerialsImported,
  disabled = false,
}) => {
  const [importMode, setImportMode] = useState<'paste' | 'upload'>('paste');
  const [serialInput, setSerialInput] = useState('');
  const [importedSerials, setImportedSerials] = useState<string[]>([]);
  const [error, setError] = useState<string>();
  const [loading, setLoading] = useState(false);

  const parseSerials = (input: string): string[] => {
    return input
      .split(/[,\n\r]+/)
      .map((s) => s.trim())
      .filter((s) => s.length > 0);
  };

  const handlePaste = () => {
    setError(undefined);
    const serials = parseSerials(serialInput);

    if (serials.length === 0) {
      setError('Please enter at least one serial number');
      return;
    }

    // Check for duplicates
    const unique = new Set(serials);
    if (unique.size !== serials.length) {
      setError('Duplicate serial numbers found. Please remove duplicates.');
      return;
    }

    setImportedSerials(serials);
    onSerialsImported?.(serials);
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setError(undefined);
    setLoading(true);

    try {
      const text = await file.text();
      const serials = parseSerials(text);

      if (serials.length === 0) {
        setError('No serial numbers found in file');
        setLoading(false);
        return;
      }

      // Check for duplicates
      const unique = new Set(serials);
      if (unique.size !== serials.length) {
        setError('Duplicate serial numbers found in file. Please remove duplicates.');
        setLoading(false);
        return;
      }

      setImportedSerials(serials);
      setSerialInput(serials.join('\n'));
      onSerialsImported?.(serials);
    } catch (err) {
      setError('Failed to read file. Make sure it contains serial numbers separated by commas or newlines.');
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveSerial = (index: number) => {
    const updated = importedSerials.filter((_, i) => i !== index);
    setImportedSerials(updated);
    setSerialInput(updated.join('\n'));
    onSerialsImported?.(updated);
  };

  const handleClearAll = () => {
    setImportedSerials([]);
    setSerialInput('');
    setError(undefined);
  };

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Import Existing Serial Numbers</h3>
        <p className="text-sm text-gray-600">
          Add serial numbers that your products already have. Enter them one per line or separated by commas.
        </p>
      </div>

      {/* Mode Selection */}
      <div className="flex gap-4">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="radio"
            checked={importMode === 'paste'}
            onChange={() => setImportMode('paste')}
            disabled={disabled}
            className="cursor-pointer"
          />
          <span className="text-gray-700">Paste Serial Numbers</span>
        </label>
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="radio"
            checked={importMode === 'upload'}
            onChange={() => setImportMode('upload')}
            disabled={disabled}
            className="cursor-pointer"
          />
          <span className="text-gray-700">Upload File (CSV/TXT)</span>
        </label>
      </div>

      {/* Paste Mode */}
      {importMode === 'paste' && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Paste Serial Numbers
          </label>
          <textarea
            value={serialInput}
            onChange={(e) => setSerialInput(e.target.value)}
            placeholder="Enter serial numbers, one per line or comma-separated&#10;Example:&#10;SN-001&#10;SN-002&#10;SN-003&#10;&#10;Or: SN-001, SN-002, SN-003"
            disabled={disabled}
            className="w-full h-32 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed resize-none"
          />
        </div>
      )}

      {/* Upload Mode */}
      {importMode === 'upload' && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Upload File
          </label>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
            <input
              type="file"
              id="serial-file-upload"
              accept=".csv,.txt"
              onChange={handleFileUpload}
              disabled={disabled || loading}
              className="hidden"
            />
            <label htmlFor="serial-file-upload" className={`cursor-pointer flex flex-col items-center gap-2 ${disabled ? 'cursor-not-allowed opacity-50' : ''}`}>
              <Upload size={32} className="text-blue-500" />
              <span className="font-medium text-gray-700">Choose file or drag and drop</span>
              <span className="text-sm text-gray-500">CSV or TXT file (serials separated by commas or newlines)</span>
            </label>
            {loading && <span className="text-sm text-blue-600 mt-2">Reading file...</span>}
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
          <AlertCircle className="text-red-600 flex-shrink-0 mt-0.5" size={18} />
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}

      {/* Action Button */}
      {importMode === 'paste' && (
        <button
          onClick={handlePaste}
          disabled={disabled || !serialInput.trim()}
          className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition font-medium"
        >
          Import Serial Numbers
        </button>
      )}

      {/* Preview */}
      {importedSerials.length > 0 && (
        <div className="space-y-3 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-green-800">
              <CheckCircle2 size={20} />
              <span className="font-medium">Imported {importedSerials.length} serial numbers</span>
            </div>
            <button
              onClick={handleClearAll}
              className="text-sm text-gray-600 hover:text-gray-800 font-medium"
            >
              Clear All
            </button>
          </div>

          <div className="space-y-2 max-h-48 overflow-y-auto">
            {importedSerials.slice(0, 10).map((serial, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between px-3 py-2 bg-green-100 rounded text-sm text-gray-800"
              >
                <span className="font-mono">{serial}</span>
                <button
                  onClick={() => handleRemoveSerial(idx)}
                  className="text-gray-600 hover:text-gray-800 transition"
                  title="Remove"
                >
                  <X size={16} />
                </button>
              </div>
            ))}
          </div>

          {importedSerials.length > 10 && (
            <p className="text-sm text-gray-600 text-center">
              ... and {importedSerials.length - 10} more serial numbers
            </p>
          )}
        </div>
      )}

      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
        <strong>Note:</strong> Imported serial numbers will be saved when you add them to the item through the item detail page.
      </div>
    </div>
  );
};

export default SerialNumberImport;
