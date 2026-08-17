import React from 'react';
import { Card, Button } from './ui';
import { X } from 'lucide-react';
import { formatDate } from '../utils/format';

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

interface ReportModalProps {
  data: ReportData;
  onClose: () => void;
}

export const ReportModal: React.FC<ReportModalProps> = ({ data, onClose }) => {
  const { orders = [], inventory = [], total_orders = 0, total_items = 0, period, calculated_at } = data;
  const overview = data.overview || (data.total_orders !== undefined ? null : null);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card padding="lg" className="max-w-4xl w-full max-h-[90vh] overflow-y-auto border-primary-300">
        <div className="flex items-center justify-between mb-4 sticky top-0 bg-white pb-4">
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
          <button onClick={onClose} className="text-neutral-400 hover:text-neutral-600 text-xl leading-none flex-shrink-0">
            <X className="w-6 h-6" />
          </button>
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
                      <td className="py-1.5 px-2">
                        <span className="px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
                          {o.status.replace(/_/g, ' ')}
                        </span>
                      </td>
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

        <div className="flex gap-2 justify-end mt-4 pt-4 border-t border-neutral-200">
          <Button
            onClick={onClose}
            className="px-4 py-2 border border-neutral-300 rounded-lg text-neutral-700 hover:bg-neutral-50"
          >
            Close
          </Button>
        </div>
      </Card>
    </div>
  );
};
