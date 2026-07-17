import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Button, Select, ListLoadingState, ListEmptyState, StatusBadge, TextInput } from '../../components/ui';
import { cardErrorPadded } from '../../styles/classNames';
import { Search, Plus, ChevronLeft, ChevronRight, AlertCircle } from 'lucide-react';
import { useInventory } from '../../hooks/useInventory';
import type { InventoryItemResponse } from '../../api/inventory';

const ITEMS_PER_PAGE = 20;

type InventoryStatus = 'parent' | 'in_stock' | 'low_stock' | 'out_of_stock';

const getStatus = (item: InventoryItemResponse): InventoryStatus => {
  if (item.children && item.children.length > 0) return 'parent';
  if (Number(item.current_quantity) === 0) return 'out_of_stock';
  if (Number(item.current_quantity) <= Number(item.minimum_quantity)) return 'low_stock';
  return 'in_stock';
};

const getStatusLabel = (status: string) => {
  return status.replace(/_/g, ' ').toUpperCase();
};

export const InventoryListPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [currentPage, setCurrentPage] = useState(1);

  const { data, isLoading, error } = useInventory(
    currentPage,
    ITEMS_PER_PAGE,
    searchQuery || undefined,
    undefined,
    selectedType === 'all' ? undefined : selectedType
  );

  const items = data?.items ?? [];
  // Separate parent items (with children), standalone items, and variants
  const parentItems = items.filter(i => !i.parent_id && i.children && i.children.length > 0);
  const standaloneItems = items.filter(i => !i.parent_id && (!i.children || i.children.length === 0));
  // Flatten for status filtering
  const displayItems = [...parentItems, ...standaloneItems];
  const filteredItems = selectedStatus === 'all'
    ? displayItems
    : displayItems.filter((item) => getStatus(item) === selectedStatus);
  const totalPages = data?.pages ?? 1;
  const totalItems = data?.total ?? 0;

  const handlePageChange = (newPage: number) => {
    if (newPage > 0 && newPage <= totalPages) {
      setCurrentPage(newPage);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  return (
    <div className="space-y-6 pb-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-neutral-900">Inventory</h1>
          <p className="text-neutral-600 mt-1">
            Manage {totalItems} items in your inventory
          </p>
        </div>
        <Button
          onClick={() => navigate('/inventory/new')}
          className="flex items-center gap-2 bg-primary-600 text-white hover:bg-primary-700"
        >
          <Plus className="w-4 h-4" />
          Add Item
        </Button>
      </div>

      {error && (
        <Card className={cardErrorPadded} padding="lg">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-error flex-shrink-0" />
            <div>
              <p className="font-medium text-error">Failed to load inventory</p>
              <p className="text-sm text-error/80">
                {error instanceof Error ? error.message : 'An error occurred'}
              </p>
            </div>
          </div>
        </Card>
      )}

      <Card padding="lg">
        <div className="space-y-4">
          {/* Search Bar */}
          <TextInput
            icon={<Search className="w-4 h-4" />}
            placeholder="Search by name, SKU, or barcode..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setCurrentPage(1);
            }}
          />

          {/* Filters */}
          <div className="flex flex-wrap gap-4">
            <div className="w-48">
              <Select
                label="Type"
                value={selectedType}
                onChange={(e) => {
                  setSelectedType(e.target.value);
                  setCurrentPage(1);
                }}
                options={[
                  { value: 'all', label: 'All Types' },
                  { value: 'consumable', label: 'Consumable' },
                  { value: 'returnable', label: 'Returnable' },
                ]}
              />
            </div>

            <div className="w-48">
              <Select
                label="Status"
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                options={[
                  { value: 'all', label: 'All Status' },
                  { value: 'in_stock', label: 'In Stock' },
                  { value: 'low_stock', label: 'Low Stock' },
                  { value: 'out_of_stock', label: 'Out of Stock' },
                ]}
              />
            </div>
          </div>
        </div>
      </Card>

      {/* Items List */}
      {isLoading ? (
        <ListLoadingState message="Loading inventory..." />
      ) : filteredItems.length === 0 ? (
        <ListEmptyState message="No items found" />
      ) : (
        <div className="space-y-3">
          {filteredItems.map((item) => {
            const status = getStatus(item);
            const children = item.children || [];
            const isParent = children.length > 0;
            const totalChildStock = children.reduce((sum, c) => sum + Number(c.current_quantity), 0);
            return (
              <div key={item.id}>
                {/* Parent or standalone item */}
                <Card
                  padding="md"
                  className={`cursor-pointer hover:shadow-md transition-shadow ${isParent ? 'border-primary-200 bg-primary-50/50' : ''}`}
                  onClick={() => navigate(`/inventory/${item.id}`)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3">
                        <div>
                          <h3 className="font-medium text-neutral-900">
                            {item.name}
                            {isParent && <span className="ml-2 text-xs text-primary-600 font-normal">(Parent Product)</span>}
                          </h3>
                          <p className="text-sm text-neutral-500">SKU: {item.sku}</p>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4 text-right">
                      <div>
                        <p className="font-semibold text-neutral-900">
                          {isParent ? `${totalChildStock} (across ${children.length} variants)` : Number(item.current_quantity)}
                        </p>
                        <p className="text-sm text-neutral-500">{children.length > 0 ? `${children.length} variant(s)` : `Min: ${Number(item.minimum_quantity)}`}</p>
                      </div>
                      <StatusBadge status={status}>{getStatusLabel(status)}</StatusBadge>
                    </div>
                  </div>
                </Card>

                {/* Children variants indented under parent */}
                {isParent && (
                  <div className="ml-6 mt-1 space-y-1 border-l-2 border-primary-200 pl-3">
                    {children.map((child) => {
                      const childStatus = getStatus(child);
                      return (
                        <Card
                          key={child.id}
                          padding="sm"
                          className="cursor-pointer hover:shadow-sm transition-shadow"
                          onClick={() => navigate(`/inventory/${child.id}`)}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex-1">
                              <h4 className="text-sm font-medium text-neutral-900">{child.name}</h4>
                              <p className="text-xs text-neutral-500">SKU: {child.sku}</p>
                            </div>
                            <div className="flex items-center gap-3 text-right">
                              <div>
                                <p className="text-sm font-semibold text-neutral-900">{Number(child.current_quantity)}</p>
                                <p className="text-xs text-neutral-500">Min: {Number(child.minimum_quantity)}</p>
                              </div>
                              <StatusBadge status={childStatus}>{getStatusLabel(childStatus)}</StatusBadge>
                            </div>
                          </div>
                        </Card>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && !isLoading && (
        <Card padding="lg">
          <div className="flex items-center justify-between">
            <p className="text-sm text-neutral-600">
              Page {currentPage} of {totalPages} ({totalItems} total items)
            </p>
            <div className="flex items-center gap-2">
              <Button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="p-2 border border-neutral-300 rounded-lg disabled:opacity-50"
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>
              <div className="text-sm font-medium text-neutral-900">
                {currentPage} / {totalPages}
              </div>
              <Button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="p-2 border border-neutral-300 rounded-lg disabled:opacity-50"
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};
