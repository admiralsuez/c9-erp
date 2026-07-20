import React, { useState, useMemo } from 'react';
import { Plus, Trash2, AlertCircle, CheckCircle2, Copy } from 'lucide-react';

interface SerialNumberInputProps {
  itemId?: number;
  onSerialsGenerated?: (serials: SerialInfo[]) => void;
  disabled?: boolean;
}

interface SerialInfo {
  serial_number: string;
  batch_id: string;
  condition: 'new' | 'used' | 'damaged' | 'refurbished';
}

type InputMode = 'single' | 'range';

export const SerialNumberInput: React.FC<SerialNumberInputProps> = ({
  itemId,
  onSerialsGenerated,
  disabled = false,
}) => {
  const [trackingEnabled, setTrackingEnabled] = useState(false);
  const [mode, setMode] = useState<InputMode>('single');
  const [condition, setCondition] = useState<'new' | 'used' | 'damaged' | 'refurbished'>('new');
  const [batchId, setBatchId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>();
  const [previewSerials, setPreviewSerials] = useState<SerialInfo[]>([]);

  // Single mode
  const [count, setCount] = useState(1);
  const [baseSerial, setBaseSerial] = useState('');

  // Range mode
  const [startSerial, setStartSerial] = useState('');
  const [endSerial, setEndSerial] = useState('');

  const previewCount = useMemo(() => {
    return Math.min(previewSerials.length, 5);
  }, [previewSerials]);

  const endPreviewCount = useMemo(() => {
    const total = previewSerials.length;
    if (total <= 10) return 0;
    return Math.min(5, total - previewCount);
  }, [previewSerials]);

  const handleGenerateSingle = async () => {
    if (!trackingEnabled || !itemId || count < 1) {
      setError('Invalid input');
      return;
    }

    setLoading(true);
    setError(undefined);

    try {
      const response = await fetch(`/api/inventory/${itemId}/serials/single`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          count,
          batch_id: batchId,
          condition,
          base_serial: baseSerial || undefined,
        }),
      });

      if (!response.ok) {
        const contentType = response.headers.get('content-type');
        let errorMessage = 'Failed to generate serials';
        
        if (contentType && contentType.includes('application/json')) {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } else {
          const text = await response.text();
          errorMessage = text || `Server error: ${response.status}`;
        }
        
        throw new Error(errorMessage);
      }

      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        throw new Error('Invalid response format from server');
      }

      const serials: SerialInfo[] = await response.json();
      
      if (!Array.isArray(serials)) {
        throw new Error('Expected array of serials from server');
      }

      setPreviewSerials(serials);
      onSerialsGenerated?.(serials);
      
      // Reset form
      setCount(1);
      setBaseSerial('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateRange = async () => {
    if (!trackingEnabled || !itemId || !startSerial || !endSerial) {
      setError('Please provide start and end serial numbers');
      return;
    }

    setLoading(true);
    setError(undefined);

    try {
      const response = await fetch(`/api/inventory/${itemId}/serials/range`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          start_serial: startSerial,
          end_serial: endSerial,
          batch_id: batchId,
          condition,
        }),
      });

      if (!response.ok) {
        const contentType = response.headers.get('content-type');
        let errorMessage = 'Failed to generate serials';
        
        if (contentType && contentType.includes('application/json')) {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } else {
          const text = await response.text();
          errorMessage = text || `Server error: ${response.status}`;
        }
        
        throw new Error(errorMessage);
      }

      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        throw new Error('Invalid response format from server');
      }

      const serials: SerialInfo[] = await response.json();
      
      if (!Array.isArray(serials)) {
        throw new Error('Expected array of serials from server');
      }

      setPreviewSerials(serials);
      onSerialsGenerated?.(serials);

      // Reset form
      setStartSerial('');
      setEndSerial('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleClearPreview = () => {
    setPreviewSerials([]);
  };

  if (!trackingEnabled) {
    return (
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Serial Number Tracking</h3>
          <p className="text-sm text-gray-600 mb-4">
            Enable this option to track individual units within this inventory item.
          </p>
        </div>

        <div className="flex items-center gap-4">
          <button
            onClick={() => setTrackingEnabled(true)}
            disabled={disabled}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition font-medium"
          >
            <Plus size={20} />
            Enable Serial Tracking
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 border border-gray-200 rounded-lg p-6 bg-gray-50">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Serial Number Tracking</h3>
          <p className="text-sm text-gray-600">Manage individual unit tracking for this item</p>
        </div>
        <button
          onClick={() => {
            setTrackingEnabled(false);
            setPreviewSerials([]);
          }}
          className="text-sm text-red-600 hover:text-red-700 font-medium"
        >
          Disable
        </button>
      </div>

      {/* Mode Selection */}
      <div className="space-y-3">
        <label className="block text-sm font-medium text-gray-700">Serial Generation Mode</label>
        <div className="flex gap-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              checked={mode === 'single'}
              onChange={() => {
                setMode('single');
                setPreviewSerials([]);
                setError(undefined);
              }}
              disabled={disabled}
              className="cursor-pointer"
            />
            <span className="text-gray-700">Individual Units</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              checked={mode === 'range'}
              onChange={() => {
                setMode('range');
                setPreviewSerials([]);
                setError(undefined);
              }}
              disabled={disabled}
              className="cursor-pointer"
            />
            <span className="text-gray-700">Serial Range</span>
          </label>
        </div>
      </div>

      {/* Common Fields */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Batch ID <span className="text-gray-500">(optional)</span>
          </label>
          <input
            type="text"
            value={batchId}
            onChange={(e) => setBatchId(e.target.value)}
            placeholder="e.g., BATCH-2024-001"
            disabled={disabled || loading}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Condition</label>
          <select
            value={condition}
            onChange={(e) => setCondition(e.target.value as any)}
            disabled={disabled || loading}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            <option value="new">New</option>
            <option value="used">Used</option>
            <option value="damaged">Damaged</option>
            <option value="refurbished">Refurbished</option>
          </select>
        </div>
      </div>

      {/* Single Mode Fields */}
      {mode === 'single' && (
        <div className="space-y-4 p-4 bg-white rounded-lg border border-gray-200">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Count
              </label>
              <input
                type="number"
                min="1"
                max="1000"
                value={count}
                onChange={(e) => setCount(Math.max(1, Number(e.target.value) || 1))}
                disabled={disabled || loading}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
              />
              <p className="text-xs text-gray-500 mt-1">Create 1-1000 individual serial numbers</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Base Serial <span className="text-gray-500">(optional)</span>
              </label>
              <input
                type="text"
                value={baseSerial}
                onChange={(e) => setBaseSerial(e.target.value)}
                placeholder="e.g., ITEM-001-"
                disabled={disabled || loading}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
              />
              <p className="text-xs text-gray-500 mt-1">Leave empty for auto-generated UUIDs</p>
            </div>
          </div>

          <button
            onClick={handleGenerateSingle}
            disabled={disabled || loading}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition font-medium flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                Generating...
              </>
            ) : (
              <>
                <Plus size={18} />
                Generate Serial Numbers
              </>
            )}
          </button>
        </div>
      )}

      {/* Range Mode Fields */}
      {mode === 'range' && (
        <div className="space-y-4 p-4 bg-white rounded-lg border border-gray-200">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Start Serial
              </label>
              <input
                type="text"
                value={startSerial}
                onChange={(e) => setStartSerial(e.target.value)}
                placeholder="e.g., SN1000 or RB-100"
                disabled={disabled || loading}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                End Serial
              </label>
              <input
                type="text"
                value={endSerial}
                onChange={(e) => setEndSerial(e.target.value)}
                placeholder="e.g., SN1099 or RB-500"
                disabled={disabled || loading}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
              />
            </div>
          </div>

          <p className="text-sm text-gray-600 bg-blue-50 p-3 rounded">
            Enter numeric ranges with same prefix (e.g., SN1000-SN1099 or RB-200-RB-500). Max 10,000 serials.
          </p>

          <button
            onClick={handleGenerateRange}
            disabled={disabled || loading}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition font-medium flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                Generating...
              </>
            ) : (
              <>
                <Plus size={18} />
                Generate Range
              </>
            )}
          </button>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
          <AlertCircle className="text-red-600 flex-shrink-0 mt-0.5" size={18} />
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}

      {/* Preview */}
      {previewSerials.length > 0 && (
        <div className="space-y-3 p-4 bg-white rounded-lg border border-green-200 bg-green-50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-green-800">
              <CheckCircle2 size={20} />
              <span className="font-medium">Generated {previewSerials.length} serial numbers</span>
            </div>
            <button
              onClick={handleClearPreview}
              className="text-sm text-gray-600 hover:text-gray-800 font-medium flex items-center gap-1"
            >
              <Trash2 size={16} />
              Clear
            </button>
          </div>

          {/* First 5 */}
          <div className="space-y-2">
            <p className="text-sm font-medium text-gray-700">First {previewCount} serials:</p>
            <div className="space-y-1">
              {previewSerials.slice(0, previewCount).map((serial, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between px-3 py-2 bg-green-100 rounded text-sm text-gray-800 font-mono"
                >
                  <span>{serial.serial_number}</span>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(serial.serial_number);
                    }}
                    className="text-gray-600 hover:text-gray-800 opacity-0 hover:opacity-100 transition"
                    title="Copy to clipboard"
                  >
                    <Copy size={14} />
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Middle indicator */}
          {previewSerials.length > 10 && (
            <div className="flex justify-center py-2">
              <span className="text-xs text-gray-500">
                ... {previewSerials.length - previewCount - endPreviewCount} more ...
              </span>
            </div>
          )}

          {/* Last 5 */}
          {endPreviewCount > 0 && (
            <div className="space-y-2">
              <p className="text-sm font-medium text-gray-700">Last {endPreviewCount} serials:</p>
              <div className="space-y-1">
                {previewSerials.slice(-endPreviewCount).map((serial, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between px-3 py-2 bg-green-100 rounded text-sm text-gray-800 font-mono"
                  >
                    <span>{serial.serial_number}</span>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(serial.serial_number);
                      }}
                      className="text-gray-600 hover:text-gray-800 opacity-0 hover:opacity-100 transition"
                      title="Copy to clipboard"
                    >
                      <Copy size={14} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SerialNumberInput;
