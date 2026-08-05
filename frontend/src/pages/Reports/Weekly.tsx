import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Button, ListLoadingState, ListEmptyState } from '../../components/ui';
import { ArrowLeft, ChevronDown, Download, AlertCircle } from 'lucide-react';
import { useInventory } from '../../hooks/useInventory';

interface SelectedVariants {
  [parentId: number]: Set<number>;
}

export const WeeklyReportPage: React.FC = () => {
  const navigate = useNavigate();
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [expandedParents, setExpandedParents] = useState<Set<number>>(new Set());
  const [selectedVariants, setSelectedVariants] = useState<SelectedVariants>({});
  const [reportView, setReportView] = useState<'config' | 'view'>('config');

  const { data: inventoryData, isLoading, error } = useInventory(1, 1000);
  const inventoryItems = inventoryData?.items ?? [];

  const parentItems = useMemo(() => {
    return inventoryItems.filter(i => !i.parent_id && i.children && i.children.length > 0);
  }, [inventoryItems]);

  const standaloneItems = useMemo(() => {
    return inventoryItems.filter(i => !i.parent_id && (!i.children || i.children.length === 0));
  }, [inventoryItems]);

  const toggleParentExpand = (parentId: number) => {
    setExpandedParents((prev) => {
      const next = new Set(prev);
      if (next.has(parentId)) {
        next.delete(parentId);
      } else {
        next.add(parentId);
      }
      return next;
    });
  };

  const toggleVariantSelect = (parentId: number, variantId: number) => {
    setSelectedVariants((prev) => {
      const next = { ...prev };
      if (!next[parentId]) next[parentId] = new Set();
      
      if (next[parentId].has(variantId)) {
        next[parentId].delete(variantId);
        if (next[parentId].size === 0) delete next[parentId];
      } else {
        next[parentId].add(variantId);
      }
      return next;
    });
  };

  const getSelectedCount = (): number => {
    let count = 0;
    Object.values(selectedVariants).forEach((set) => {
      count += set.size;
    });
    return count;
  };

  const handleGenerateReport = async () => {
    if (!dateFrom || !dateTo) {
      alert('Please select both start and end dates');
      return;
    }
    if (getSelectedCount() === 0) {
      alert('Please select at least one variant');
      return;
    }
    
    try {
      // Collect all selected variant IDs
      const variantIds = Object.entries(selectedVariants)
        .flatMap(([_, variants]) => Array.from(variants));
      
      // Call backend to generate report
      const params = new URLSearchParams();
      params.set('date_from', dateFrom);
      params.set('date_to', dateTo);
      params.set('format', 'json');
      variantIds.forEach(id => params.append('variant_ids', String(id)));
      
      const response = await fetch(`/api/reports/custom?${params.toString()}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      
      if (!response.ok) {
        throw new Error('Failed to generate report');
      }
      
      const data = await response.json();
      // TODO: Store report data and display in view mode
      console.log('Report data:', data);
      setReportView('view');
    } catch (error) {
      alert(`Error generating report: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  return (
    <div className="space-y-6 pb-6">
      <div className="flex items-center gap-4">
        <button onClick={() => navigate('/inventory')} className="p-2 hover:bg-neutral-100 rounded-lg">
          <ArrowLeft className="w-5 h-5 text-neutral-600" />
        </button>
        <div>
          <h1 className="text-3xl font-bold text-neutral-900">Weekly Report</h1>
          <p className="text-neutral-600 mt-1">Generate inventory reports</p>
        </div>
      </div>

      {error && (
        <Card className="bg-error/10 border border-error" padding="lg">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-error" />
            <p className="text-error">Failed to load inventory</p>
          </div>
        </Card>
      )}

      {reportView === 'config' ? (
        <>
          <Card padding="lg">
            <h2 className="text-lg font-semibold text-neutral-900 mb-4">Configuration</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-2">From Date</label>
                <input
                  type="date"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-2">To Date</label>
                <input
                  type="date"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm"
                />
              </div>
            </div>
          </Card>

          <Card padding="lg">
            <h2 className="text-lg font-semibold text-neutral-900 mb-3">
              Select Variants ({getSelectedCount()} selected)
            </h2>
            <p className="text-sm text-neutral-600 mb-3">Click parent to expand and select children</p>

            {isLoading ? (
              <ListLoadingState message="Loading..." />
            ) : inventoryItems.length === 0 ? (
              <ListEmptyState message="No items found" />
            ) : (
              <div className="space-y-2">
                {parentItems.map((parent) => {
                  const isExpanded = expandedParents.has(parent.id);
                  const children = parent.children || [];
                  const count = selectedVariants[parent.id]?.size || 0;
                  
                  return (
                    <div key={parent.id}>
                      <div className="flex items-center gap-2 p-2 bg-neutral-50 rounded border border-neutral-200">
                        <button
                          type="button"
                          onClick={() => toggleParentExpand(parent.id)}
                          className="p-1 hover:bg-neutral-200 rounded"
                        >
                          <ChevronDown
                            className={`w-4 h-4 transition-transform ${
                              isExpanded ? 'rotate-0' : '-rotate-90'
                            }`}
                          />
                        </button>
                        <div className="flex-1">
                          <p className="text-sm font-medium text-neutral-900">{parent.name}</p>
                          <p className="text-xs text-neutral-500">SKU: {parent.sku}</p>
                        </div>
                        <span className="text-xs text-neutral-600 bg-neutral-200 px-2 py-1 rounded">
                          {count} / {children.length}
                        </span>
                      </div>

                      {isExpanded && (
                        <div className="ml-4 mt-1 space-y-1 border-l-2 border-primary-200 pl-3">
                          {children.map((child) => {
                            const isSelected = selectedVariants[parent.id]?.has(child.id) || false;
                            return (
                              <label key={child.id} className="flex items-center gap-2 p-2 rounded hover:bg-neutral-50 cursor-pointer">
                                <input
                                  type="checkbox"
                                  checked={isSelected}
                                  onChange={() => toggleVariantSelect(parent.id, child.id)}
                                  className="w-4 h-4 rounded border-neutral-300 text-primary-600"
                                />
                                <div className="flex-1 min-w-0">
                                  <p className="text-sm text-neutral-900">{child.name}</p>
                                  <p className="text-xs text-neutral-500">SKU: {child.sku}</p>
                                </div>
                              </label>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  );
                })}

                {standaloneItems.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-neutral-200">
                    <p className="text-sm font-medium text-neutral-900 mb-2">Standalone Items</p>
                    <div className="space-y-2">
                      {standaloneItems.map((item) => {
                        const isSelected = selectedVariants[item.id]?.has(item.id) || false;
                        return (
                          <label key={item.id} className="flex items-center gap-2 p-2 border border-neutral-200 rounded hover:border-primary-300 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => toggleVariantSelect(item.id, item.id)}
                              className="w-4 h-4 rounded border-neutral-300 text-primary-600"
                            />
                            <div className="flex-1 min-w-0">
                              <p className="text-sm text-neutral-900">{item.name}</p>
                              <p className="text-xs text-neutral-500">SKU: {item.sku}</p>
                            </div>
                          </label>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            )}
          </Card>

          <div className="flex gap-3 justify-end">
            <Button onClick={() => navigate('/inventory')} className="px-4 py-2 border border-neutral-300 rounded-lg hover:bg-neutral-50">
              Cancel
            </Button>
            <Button
              onClick={handleGenerateReport}
              disabled={getSelectedCount() === 0 || !dateFrom || !dateTo}
              className="px-4 py-2 bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50 flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              Generate Report
            </Button>
          </div>
        </>
      ) : (
        <Card padding="lg">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-neutral-900">Report</h2>
            <Button onClick={() => setReportView('config')} className="text-sm border border-neutral-300 hover:bg-neutral-50">
              Back
            </Button>
          </div>
          <p className="text-neutral-600 mb-4">
            Report from {dateFrom} to {dateTo} ({getSelectedCount()} variants)
          </p>
          <div className="p-4 bg-neutral-50 rounded-lg text-center text-neutral-500">
            <p>Report data will be displayed here</p>
          </div>
        </Card>
      )}
    </div>
  );
};

export default WeeklyReportPage;
