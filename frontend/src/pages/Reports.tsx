import React, { useState, useMemo } from 'react';
import { Card, Button, FilterPill, SearchInput, CheckboxInput, FormGroup, StatusBadge } from '../components/ui';
import { FileText, Loader, Download, Calendar, Filter, FileSpreadsheet, X, Eye } from 'lucide-react';
import { apiClient } from '../api/client';
import { useInventory } from '../hooks/useInventory';
import { useVendors } from '../hooks/useVendors';
import { formatDate } from '../utils/format';

const todayStr = () => new Date().toISOString().split('T')[0];

const downloadBlob = (blob: Blob, filename: string) => {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
};

interface ReportData {
  overview?: { total_orders: number; pending_approvals: number; recent_orders: any[] };
  order_metrics?: any;
  inventory_health?: any;
  vendor_performance?: any;
  orders?: any[];
  inventory?: any[];
  total_orders?: number;
  total_items?: number;
  period?: { label: string; start: string; end: string };
  calculated_at?: string;
}

export const ReportsPage: React.FC = () => {
  const [generating, setGenerating] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reportData, setReportData] = useState<ReportData | null>(null);

  const generateReport = async (period: 'weekly' | 'monthly', action: 'view' | 'download') => {
    setGenerating(`${period}-${action}`);
    setError(null);
    if (action === 'view') setReportData(null);
    try {
      const fmt = action === 'view' ? 'json' : 'pdf';
      const response = await apiClient.post(
        `/reports/generate?period=${period}&format=${fmt}`,
        {},
        action === 'view' ? {} : { responseType: 'blob' }
      );
      if (action === 'view') {
        setReportData(response.data);
      } else {
        const filename = `${period}_report_${new Date().toISOString().split('T')[0]}.pdf`;
        downloadBlob(response.data, filename);
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to generate report');
    } finally {
      setGenerating(null);
    }
  };

  // Custom report state
  const [customDateFrom, setCustomDateFrom] = useState(todayStr());
  const [customDateTo, setCustomDateTo] = useState(todayStr());
  const [selectedItemIds, setSelectedItemIds] = useState<Set<number>>(new Set());
  const [selectedVendorIds, setSelectedVendorIds] = useState<Set<number>>(new Set());
  const [customFormat, setCustomFormat] = useState<'pdf' | 'excel'>('pdf');
  const [customGenerating, setCustomGenerating] = useState<string | null>(null);
  const [customError, setCustomError] = useState<string | null>(null);
  const [itemSearch, setItemSearch] = useState('');
  const [vendorSearch, setVendorSearch] = useState('');
  const { data: inventoryData, isLoading: invLoading } = useInventory(1, 100);
  const { data: vendorsData, isLoading: venLoading } = useVendors(1, 100);

  const toggleItem = (id: number) => {
    setSelectedItemIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const toggleVendor = (id: number) => {
    setSelectedVendorIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const filteredItems = useMemo(() => {
    const items = inventoryData?.items ?? [];
    if (!itemSearch) return items;
    const q = itemSearch.toLowerCase();
    return items.filter((i: any) =>
      i.sku?.toLowerCase().includes(q) || i.name?.toLowerCase().includes(q)
    );
  }, [inventoryData, itemSearch]);

  const filteredVendors = useMemo(() => {
    const vendors = vendorsData?.items ?? [];
    if (!vendorSearch) return vendors;
    const q = vendorSearch.toLowerCase();
    return vendors.filter((v: any) =>
      v.name?.toLowerCase().includes(q)
    );
  }, [vendorsData, vendorSearch]);

  const generateCustomReport = async (action: 'view' | 'download') => {
    if (!customDateFrom || !customDateTo) {
      setCustomError('Please select a date range');
      return;
    }
    const key = `${action}-${customFormat}`;
    setCustomGenerating(key);
    setCustomError(null);
    if (action === 'view') setReportData(null);
    try {
      const params = new URLSearchParams();
      params.set('date_from', customDateFrom);
      params.set('date_to', customDateTo);
      const fmt = action === 'view' ? 'json' : customFormat;
      params.set('format', fmt);
      for (const id of selectedItemIds) params.append('item_ids', String(id));
      for (const id of selectedVendorIds) params.append('vendor_ids', String(id));
      const response = await apiClient.post(
        `/reports/custom?${params.toString()}`,
        {},
        action === 'view' ? {} : { responseType: 'blob' }
      );
      if (action === 'view') {
        setReportData(response.data);
      } else {
        const ext = customFormat === 'excel' ? 'xlsx' : 'pdf';
        const filename = `custom_report_${customDateTo}.${ext}`;
        downloadBlob(response.data, filename);
      }
    } catch (err: any) {
      setCustomError(err?.response?.data?.detail || err?.message || 'Failed to generate custom report');
    } finally {
      setCustomGenerating(null);
    }
  };

  const isGen = (key: string) => generating === key;
  const isCustomGen = (key: string) => customGenerating === key;

  return (
    <div className="space-y-6 pb-6">
      <div>
        <h1 className="text-3xl font-bold text-neutral-900">Reports</h1>
        <p className="text-neutral-600 mt-1">Generate periodic or custom reports for orders and inventory.</p>
      </div>

      {error && (
        <Card padding="md" className="bg-error/10 border border-error/30">
          <p className="text-sm text-error">{error}</p>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card padding="lg" className="hover:shadow-md transition-shadow">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-lg bg-primary-50 flex items-center justify-center flex-shrink-0">
              <Calendar className="w-6 h-6 text-primary-600" />
            </div>
            <div className="flex-1">
              <h2 className="text-lg font-semibold text-neutral-900">Weekly Report</h2>
              <p className="text-sm text-neutral-600 mt-1">
                Orders placed, inventory changes, vendor performance, and user activity over the last 7 days.
              </p>
              <div className="mt-4 flex gap-2">
                <Button
                  onClick={() => generateReport('weekly', 'view')}
                  disabled={isGen('weekly-view')}
                  className="px-3 py-2 bg-primary-600 text-white hover:bg-primary-700 text-sm disabled:opacity-50 flex items-center gap-2"
                >
                  {isGen('weekly-view') ? (
                    <><Loader className="w-4 h-4 animate-spin" /> Loading...</>
                  ) : (
                    <><Eye className="w-4 h-4" /> View</>
                  )}
                </Button>
                <Button
                  onClick={() => generateReport('weekly', 'download')}
                  disabled={isGen('weekly-download')}
                  variant="secondary"
                  className="px-3 py-2 text-sm flex items-center gap-2"
                >
                  {isGen('weekly-download') ? (
                    <><Loader className="w-4 h-4 animate-spin" /> Loading...</>
                  ) : (
                    <><Download className="w-4 h-4" /> Download</>
                  )}
                </Button>
              </div>
            </div>
          </div>
        </Card>

        <Card padding="lg" className="hover:shadow-md transition-shadow">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-lg bg-info/10 flex items-center justify-center flex-shrink-0">
              <FileText className="w-6 h-6 text-info" />
            </div>
            <div className="flex-1">
              <h2 className="text-lg font-semibold text-neutral-900">Monthly Report</h2>
              <p className="text-sm text-neutral-600 mt-1">
                Comprehensive overview of all orders, inventory health, vendor delivery performance, and user activity over the last 30 days.
              </p>
              <div className="mt-4 flex gap-2">
                <Button
                  onClick={() => generateReport('monthly', 'view')}
                  disabled={isGen('monthly-view')}
                  className="px-3 py-2 bg-info text-white hover:bg-info/90 text-sm disabled:opacity-50 flex items-center gap-2"
                >
                  {isGen('monthly-view') ? (
                    <><Loader className="w-4 h-4 animate-spin" /> Loading...</>
                  ) : (
                    <><Eye className="w-4 h-4" /> View</>
                  )}
                </Button>
                <Button
                  onClick={() => generateReport('monthly', 'download')}
                  disabled={isGen('monthly-download')}
                  variant="secondary"
                  className="px-3 py-2 text-sm flex items-center gap-2"
                >
                  {isGen('monthly-download') ? (
                    <><Loader className="w-4 h-4 animate-spin" /> Loading...</>
                  ) : (
                    <><Download className="w-4 h-4" /> Download</>
                  )}
                </Button>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Custom Report Section */}
      <Card padding="lg" className="border-primary-200 hover:shadow-md transition-shadow">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-lg bg-accent/10 flex items-center justify-center flex-shrink-0">
            <Filter className="w-6 h-6 text-accent" />
          </div>
          <div className="flex-1">
            <h2 className="text-lg font-semibold text-neutral-900">Custom Report</h2>
            <p className="text-sm text-neutral-600 mt-1">
              Filter by date range, specific items, and vendors. Leave filters empty to include all.
            </p>
          </div>
        </div>

        {customError && (
          <div className="mt-4 p-3 bg-error/10 border border-error/30 rounded-lg">
            <p className="text-sm text-error">{customError}</p>
          </div>
        )}

        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <FormGroup label="Date Range">
              <div className="flex gap-2 mb-2 flex-wrap">
                {[
                  { label: 'Today', days: 0 },
                  { label: 'This Week', days: 7 },
                  { label: 'This Month', days: 30 },
                  { label: 'This Quarter', days: 90 },
                ].map(p => (
                  <FilterPill
                    key={p.label}
                    onClick={() => {
                      const to = new Date();
                      const from = new Date();
                      if (p.days > 0) from.setDate(from.getDate() - p.days);
                      setCustomDateTo(to.toISOString().split('T')[0]);
                      setCustomDateFrom(from.toISOString().split('T')[0]);
                    }}
                  >
                    {p.label}
                  </FilterPill>
                ))}
              </div>
              <div className="grid grid-cols-2 gap-2">
                <input
                  type="date"
                  value={customDateFrom}
                  onChange={e => setCustomDateFrom(e.target.value)}
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
                <input
                  type="date"
                  value={customDateTo}
                  onChange={e => setCustomDateTo(e.target.value)}
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
            </FormGroup>
          </div>
          <div>
            <FormGroup label={`Items${selectedItemIds.size > 0 ? ` (${selectedItemIds.size} selected)` : ''}`}>
              <SearchInput
                value={itemSearch}
                onChange={e => setItemSearch(e.target.value)}
                placeholder="Search by SKU or name..."
              />
              <div className="max-h-40 overflow-y-auto border border-neutral-200 rounded-lg divide-y divide-neutral-100 mt-1">
                {invLoading ? (
                  <p className="text-xs text-neutral-400 p-2 text-center">Loading...</p>
                ) : filteredItems.length === 0 ? (
                  <p className="text-xs text-neutral-400 p-2">No items found</p>
                ) : (
                  filteredItems.map((item: any) => (
                    <CheckboxInput
                      key={item.id}
                      checked={selectedItemIds.has(item.id)}
                      onChange={() => toggleItem(item.id)}
                      label={
                        <><span className="font-mono text-neutral-500">{item.sku}</span><span className="text-neutral-700 truncate ml-1">{item.name}</span></>
                      }
                    />
                  ))
                )}
              </div>
              {selectedItemIds.size > 0 && (
                <button onClick={() => setSelectedItemIds(new Set())} className="text-xs text-error hover:text-error/80 mt-1 flex items-center gap-1">
                  <X className="w-3 h-3" /> Clear selection
                </button>
              )}
            </FormGroup>
          </div>
          <div>
            <FormGroup label={`Vendors${selectedVendorIds.size > 0 ? ` (${selectedVendorIds.size} selected)` : ''}`}>
              <SearchInput
                value={vendorSearch}
                onChange={e => setVendorSearch(e.target.value)}
                placeholder="Search by name..."
              />
              <div className="max-h-40 overflow-y-auto border border-neutral-200 rounded-lg divide-y divide-neutral-100 mt-1">
                {venLoading ? (
                  <p className="text-xs text-neutral-400 p-2 text-center">Loading...</p>
                ) : filteredVendors.length === 0 ? (
                  <p className="text-xs text-neutral-400 p-2">No vendors found</p>
                ) : (
                  filteredVendors.map((v: any) => (
                    <CheckboxInput
                      key={v.id}
                      checked={selectedVendorIds.has(v.id)}
                      onChange={() => toggleVendor(v.id)}
                      label={v.name}
                    />
                  ))
                )}
              </div>
              {selectedVendorIds.size > 0 && (
                <button onClick={() => setSelectedVendorIds(new Set())} className="text-xs text-error hover:text-error/80 mt-1 flex items-center gap-1">
                  <X className="w-3 h-3" /> Clear selection
                </button>
              )}
            </FormGroup>
          </div>
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-1">Format</label>
            <select
              value={customFormat}
              onChange={e => setCustomFormat(e.target.value as 'pdf' | 'excel')}
              className="w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="pdf">PDF</option>
              <option value="excel">Excel (.xlsx)</option>
            </select>
          </div>
          <div className="flex items-end gap-2">
            <Button
              onClick={() => generateCustomReport('view')}
              disabled={isCustomGen('view-pdf') || isCustomGen('view-excel')}
              className="flex-1 px-3 py-2 bg-primary-600 text-white hover:bg-primary-700 text-sm disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {isCustomGen('view-pdf') || isCustomGen('view-excel') ? (
                <><Loader className="w-4 h-4 animate-spin" /> Loading...</>
              ) : (
                <><Eye className="w-4 h-4" /> View</>
              )}
            </Button>
            <Button
              onClick={() => generateCustomReport('download')}
              disabled={isCustomGen('download-pdf') || isCustomGen('download-excel')}
              variant="secondary"
              className="flex-1 px-3 py-2 text-sm flex items-center justify-center gap-2"
            >
              {isCustomGen('download-pdf') || isCustomGen('download-excel') ? (
                <><Loader className="w-4 h-4 animate-spin" /> Loading...</>
              ) : customFormat === 'excel' ? (
                <><FileSpreadsheet className="w-4 h-4" /> Download</>
              ) : (
                <><Download className="w-4 h-4" /> Download</>
              )}
            </Button>
          </div>
        </div>
      </Card>

      {/* Report Results */}
      {reportData && (
        <ReportResults data={reportData} onClose={() => setReportData(null)} />
      )}

      <Card padding="lg" className="bg-neutral-50 border-neutral-200">
        <h3 className="text-sm font-semibold text-neutral-900 mb-3">What's included in each report</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-neutral-600">
          <ul className="space-y-1.5 list-disc list-inside">
            <li>Order metrics — total orders, status breakdown, pending approvals</li>
            <li>Average approval and dispatch times</li>
            <li>Inventory health — total items, low stock alerts</li>
          </ul>
          <ul className="space-y-1.5 list-disc list-inside">
            <li>Vendor performance — top vendors, delivery on-time percentage</li>
            <li>User activity — active users, actions performed, orders created</li>
            <li>Email statistics — sent, delivered, failed counts</li>
          </ul>
        </div>
      </Card>
    </div>
  );
};

/* ============ In-App Report View ============ */

const ReportResults = ({ data, onClose }: { data: ReportData; onClose: () => void }) => {
  const { orders = [], inventory = [], total_orders = 0, total_items = 0, period, calculated_at } = data;
  const overview = data.overview || (data.total_orders !== undefined ? null : null);

  return (
    <Card padding="lg" className="border-primary-300">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-neutral-900">
            {period?.label || 'Custom'} Report
          </h2>
          {period && (
            <p className="text-xs text-neutral-500">
              {period.start} → {period.end}
              {calculated_at && ` · Generated ${formatDate(calculated_at)}`}
            </p>
          )}
        </div>
        <button onClick={onClose} className="text-neutral-400 hover:text-neutral-600 text-xl leading-none">&times;</button>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        <div className="p-3 bg-primary-50 rounded-lg border border-primary-100">
          <p className="text-xs text-primary-700 font-medium">Total Orders</p>
          <p className="text-2xl font-bold text-primary-900">{total_orders}</p>
        </div>
        {overview && (
          <div className="p-3 bg-warning/10 rounded-lg border border-warning/20">
            <p className="text-xs text-warning-700 font-medium">Pending Approvals</p>
            <p className="text-2xl font-bold text-warning-800">{overview.pending_approvals}</p>
          </div>
        )}
        <div className="p-3 bg-info/10 rounded-lg border border-info/20">
          <p className="text-xs text-info-700 font-medium">Total Items</p>
          <p className="text-2xl font-bold text-info-800">{total_items}</p>
        </div>
      </div>

      {/* Orders table */}
      {orders.length > 0 && (
        <div className="mb-4">
          <h3 className="text-sm font-semibold text-neutral-900 mb-2">Orders ({orders.length})</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-neutral-200">
                  <th className="text-left py-2 px-2 font-semibold text-neutral-700">Order #</th>
                  <th className="text-left py-2 px-2 font-semibold text-neutral-700">Vendor</th>
                  <th className="text-left py-2 px-2 font-semibold text-neutral-700">Status</th>
                  <th className="text-right py-2 px-2 font-semibold text-neutral-700">Items</th>
                  <th className="text-left py-2 px-2 font-semibold text-neutral-700">Date</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((o: any) => (
                  <tr key={o.id} className="border-b border-neutral-100">
                    <td className="py-1.5 px-2 font-mono text-primary-600">{o.order_number}</td>
                    <td className="py-1.5 px-2">{o.vendor_name}</td>
                    <td className="py-1.5 px-2"><StatusBadge status={o.status}>{o.status.replace(/_/g, ' ')}</StatusBadge></td>
                    <td className="py-1.5 px-2 text-right">{o.item_count}</td>
                    <td className="py-1.5 px-2 text-neutral-500 text-xs">{formatDate(o.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Inventory table */}
      {inventory.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-neutral-900 mb-2">Inventory ({inventory.length})</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-neutral-200">
                  <th className="text-left py-2 px-2 font-semibold text-neutral-700">SKU</th>
                  <th className="text-left py-2 px-2 font-semibold text-neutral-700">Name</th>
                  <th className="text-right py-2 px-2 font-semibold text-neutral-700">On Hand</th>
                  <th className="text-right py-2 px-2 font-semibold text-neutral-700">Reserved</th>
                  <th className="text-right py-2 px-2 font-semibold text-neutral-700">Min Stock</th>
                  <th className="text-left py-2 px-2 font-semibold text-neutral-700">Category</th>
                </tr>
              </thead>
              <tbody>
                {inventory.map((i: any) => (
                  <tr key={i.id} className="border-b border-neutral-100">
                    <td className="py-1.5 px-2 font-mono text-xs text-neutral-600">{i.sku}</td>
                    <td className="py-1.5 px-2">{i.name}</td>
                    <td className="py-1.5 px-2 text-right">{i.current_quantity}</td>
                    <td className="py-1.5 px-2 text-right">{i.reserved_quantity}</td>
                    <td className="py-1.5 px-2 text-right">{i.minimum_quantity}</td>
                    <td className="py-1.5 px-2 text-neutral-500 text-xs">{i.category || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {orders.length === 0 && inventory.length === 0 && (
        <p className="text-sm text-neutral-500 text-center py-6">No data found for the selected period.</p>
      )}
    </Card>
  );
};

export default ReportsPage;