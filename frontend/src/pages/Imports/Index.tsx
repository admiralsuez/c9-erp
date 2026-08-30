import React, { useState } from 'react';
import { Card, Button } from '../../components/ui';
import { Upload, Download, CheckCircle, AlertCircle, Loader } from 'lucide-react';
import { ErrorBanner } from '../../components/ErrorAlert';
import toast from 'react-hot-toast';

interface ImportResult {
  success: boolean;
  total_rows: number;
  successful: number;
  failed: number;
  errors: Array<{
    row_number: number;
    reason: string;
    values?: Record<string, any>;
  }>;
  message: string;
}

type ImportType = 'vendors' | 'items' | 'orders';

const ImportSection: React.FC<{
  title: string;
  description: string;
  importType: ImportType;
  onImport: (type: ImportType, file: File) => Promise<void>;
  isLoading: boolean;
  result?: ImportResult;
  error?: any;
}> = ({ title, description, importType, onImport, isLoading, result, error }) => {
  const [file, setFile] = useState<File | null>(null);

  const handleTemplateDownload = () => {
    // Fetch template from backend
    fetch(`/api/${importType === 'vendors' ? 'vendors' : importType === 'items' ? 'inventory/items' : 'orders'}/import/template`)
      .then(res => res.json())
      .then(data => {
        // Create CSV content
        const headers = data.headers.join(',');
        const rows = data.sample_rows.map((row: string[]) =>
          row.map((cell: string) => `"${cell}"`).join(',')
        ).join('\n');
        const csv = `${headers}\n${rows}`;

        // Download
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = data.filename;
        a.click();
        URL.revokeObjectURL(url);
        toast.success('Template downloaded');
      })
      .catch(() => toast.error('Failed to download template'));
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleImport = async () => {
    if (!file) {
      toast.error('Please select a file');
      return;
    }
    await onImport(importType, file);
    setFile(null);
  };

  return (
    <Card padding="lg" className="border-l-4 border-primary-600">
      <div className="space-y-4">
        <div>
          <h2 className="text-lg font-semibold text-neutral-900">{title}</h2>
          <p className="text-sm text-neutral-600 mt-1">{description}</p>
        </div>

        {error && (
          <ErrorBanner
            error={error}
            onDismiss={() => {}}
          />
        )}

        {result && (
          <div className={`p-4 rounded-lg ${result.success ? 'bg-success/10 border border-success/30' : 'bg-warning/10 border border-warning/30'}`}>
            <div className="flex items-start gap-3">
              {result.success ? (
                <CheckCircle className="w-5 h-5 text-success flex-shrink-0 mt-0.5" />
              ) : (
                <AlertCircle className="w-5 h-5 text-warning flex-shrink-0 mt-0.5" />
              )}
              <div className="flex-1">
                <h3 className={`font-semibold ${result.success ? 'text-success' : 'text-warning'}`}>
                  {result.message}
                </h3>
                <div className="mt-2 text-sm space-y-1">
                  <p>✅ Successful: <span className="font-medium">{result.successful}</span></p>
                  {result.failed > 0 && (
                    <p>❌ Failed: <span className="font-medium">{result.failed}</span></p>
                  )}
                </div>

                {result.errors.length > 0 && (
                  <div className="mt-3 space-y-2 max-h-48 overflow-y-auto">
                    <p className="font-medium text-xs text-neutral-700">Errors:</p>
                    {result.errors.slice(0, 5).map((err, idx) => (
                      <div key={idx} className="text-xs bg-neutral-50 p-2 rounded border border-neutral-200">
                        <p className="font-semibold text-neutral-900">Row {err.row_number}: {err.reason}</p>
                      </div>
                    ))}
                    {result.errors.length > 5 && (
                      <p className="text-xs text-neutral-500 italic">
                        ... and {result.errors.length - 5} more errors
                      </p>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-2">
              CSV File
            </label>
            <input
              type="file"
              accept=".csv"
              onChange={handleFileSelect}
              disabled={isLoading}
              className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
            />
            <p className="text-xs text-neutral-500 mt-1">
              {file ? `Selected: ${file.name}` : 'Select a CSV file to import'}
            </p>
          </div>

          <div className="flex gap-2">
            <Button
              onClick={handleTemplateDownload}
              disabled={isLoading}
              className="flex items-center gap-2 border border-neutral-300 text-neutral-700 hover:bg-neutral-50 flex-1"
            >
              <Download className="w-4 h-4" />
              Download Template
            </Button>
            <Button
              onClick={handleImport}
              disabled={isLoading || !file}
              className="flex items-center gap-2 bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50 flex-1"
            >
              {isLoading ? (
                <Loader className="w-4 h-4 animate-spin" />
              ) : (
                <Upload className="w-4 h-4" />
              )}
              {isLoading ? 'Importing...' : 'Import'}
            </Button>
          </div>
        </div>
      </div>
    </Card>
  );
};

export const ImportsPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<Record<ImportType, ImportResult | undefined>>({
    vendors: undefined,
    items: undefined,
    orders: undefined,
  });
  const [errors, setErrors] = useState<Record<ImportType, any>>({
    vendors: undefined,
    items: undefined,
    orders: undefined,
  });

  const handleImport = async (type: ImportType, file: File) => {
    setLoading(true);
    setErrors(prev => ({ ...prev, [type]: undefined }));

    try {
      const formData = new FormData();
      formData.append('file', file);

      const endpoint = type === 'vendors'
        ? '/api/vendors/import'
        : type === 'items'
        ? '/api/inventory/items/import'
        : '/api/orders/import';

      // Get token from localStorage
      const token = localStorage.getItem('access_token');
      if (!token) {
        throw new Error('Not authenticated. Please log in.');
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Import failed');
      }

      setResults(prev => ({ ...prev, [type]: data }));

      if (data.success) {
        toast.success(data.message);
      } else {
        toast.error(data.message);
      }
    } catch (err: any) {
      const error = {
        response: {
          status: 400,
          data: { detail: err.message || 'Import failed' },
        },
      };
      setErrors(prev => ({ ...prev, [type]: error }));
      toast.error(err.message || 'Import failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 pb-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-neutral-900">Bulk Import</h1>
        <p className="text-neutral-600 mt-1">
          Import vendors, items, and orders from CSV files
        </p>
      </div>

      {/* Import Sections */}
      <div className="space-y-4">
        <ImportSection
          title="Import Vendors"
          description="Upload a CSV file with vendor information. Download the template to see the required format."
          importType="vendors"
          onImport={handleImport}
          isLoading={loading}
          result={results.vendors}
          error={errors.vendors}
        />

        <ImportSection
          title="Import Items"
          description="Upload a CSV file with inventory items. Includes SKU, quantity, category, and more."
          importType="items"
          onImport={handleImport}
          isLoading={loading}
          result={results.items}
          error={errors.items}
        />

        <ImportSection
          title="Import Orders"
          description="Upload a CSV file with purchase orders. Includes vendor, item, quantity, and dates."
          importType="orders"
          onImport={handleImport}
          isLoading={loading}
          result={results.orders}
          error={errors.orders}
        />
      </div>

      {/* Info Banner */}
      <Card className="bg-blue-50 border border-blue-200" padding="lg">
        <div className="flex gap-3">
          <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-blue-900">Import Tips</h3>
            <ul className="text-sm text-blue-800 mt-2 space-y-1">
              <li>• Download the template first to see the required columns and format</li>
              <li>• Ensure CSV files are properly formatted with headers in the first row</li>
              <li>• The import will show errors by row number for easy fixing</li>
              <li>• Valid rows are imported even if some rows have errors</li>
              <li>• Duplicate vendors and items are automatically detected and skipped</li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  );
};
