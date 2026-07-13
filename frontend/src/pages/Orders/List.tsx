import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Button, Select, DateInput, FilterPill, ListLoadingState, ListEmptyState, StatusBadge, TextInput } from '../../components/ui';
import { cardErrorPadded } from '../../styles/classNames';
import { Search, Plus, ChevronLeft, ChevronRight, AlertCircle, Filter } from 'lucide-react';
import { useOrders } from '../../hooks/useOrders';
import { formatDate } from '../../utils/format';

const toDateInput = (d: Date) => d.toISOString().split('T')[0];

const getDateRange = (range: 'today' | 'this_week' | 'this_month' | 'last_month' | 'this_fy') => {
  const now = new Date();
  const y = now.getFullYear();
  const m = now.getMonth();

  switch (range) {
    case 'today':
      return { from: toDateInput(now), to: toDateInput(now) };
    case 'this_week': {
      const day = now.getDay();
      const mon = new Date(now);
      mon.setDate(now.getDate() - (day === 0 ? 6 : day - 1));
      return { from: toDateInput(mon), to: toDateInput(now) };
    }
    case 'this_month':
      return { from: toDateInput(new Date(y, m, 1)), to: toDateInput(now) };
    case 'last_month':
      return {
        from: toDateInput(new Date(y, m - 1, 1)),
        to: toDateInput(new Date(y, m, 0)),
      };
    case 'this_fy': {
      const fyStart = m < 3 ? new Date(y - 1, 3, 1) : new Date(y, 3, 1);
      return { from: toDateInput(fyStart), to: toDateInput(now) };
    }
  }
};

const ORDERS_PER_PAGE = 20;

const formatStatus = (status: string) =>
  status.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

export const OrdersListPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('open');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [sortBy, setSortBy] = useState('recent_activity');
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    setCurrentPage(1);
  }, [selectedStatus, sortBy]);

  const { data, isLoading, error } = useOrders(
    currentPage,
    ORDERS_PER_PAGE,
    selectedStatus === 'all' || selectedStatus === 'open' ? undefined : selectedStatus,
    searchQuery || undefined,
    dateFrom || undefined,
    dateTo || undefined,
    sortBy,
    selectedStatus === 'open' ? 'closed,cancelled' : undefined
  );

  const items = data?.items ?? [];
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
          <h1 className="text-3xl font-bold text-neutral-900">Orders</h1>
          <p className="text-neutral-600 mt-1">Manage purchase orders ({totalItems} orders)</p>
        </div>
        <Button
          onClick={() => navigate('/orders/new')}
          className="flex items-center gap-2 bg-primary-600 text-white hover:bg-primary-700"
        >
          <Plus className="w-4 h-4" />
          Create Order
        </Button>
      </div>

      {error && (
        <Card className={cardErrorPadded} padding="lg">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-error flex-shrink-0" />
            <div>
              <p className="font-medium text-error">Failed to load orders</p>
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
            placeholder="Search by order number or vendor..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setCurrentPage(1);
            }}
          />

          {/* Quick Filters */}
          <div className="flex flex-wrap gap-2">
            <FilterPill active={selectedStatus === 'all'} onClick={() => { setSelectedStatus('all'); setCurrentPage(1); }}>
              All Orders
            </FilterPill>
            <FilterPill active={selectedStatus === 'open'} onClick={() => { setSelectedStatus('open'); setCurrentPage(1); }}>
              Open Orders
            </FilterPill>
            <FilterPill active={selectedStatus === 'closed'} onClick={() => { setSelectedStatus('closed'); setCurrentPage(1); }}>
              Closed Orders
            </FilterPill>
          </div>

          {/* Sort and Filter Controls */}
          <div className="flex items-center gap-4">
            <span className="text-sm text-neutral-500 whitespace-nowrap">Sort:</span>
            <select
              value={sortBy}
              onChange={(e) => {
                setSortBy(e.target.value);
                setCurrentPage(1);
              }}
              className="text-sm px-2 py-1 border border-neutral-300 rounded focus:outline-none focus:ring-1 focus:ring-primary-500"
            >
              <option value="recent_activity">Most Recent Activity</option>
              <option value="created_date">Most Recently Created</option>
            </select>
            <button
              type="button"
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center gap-1.5 text-xs font-medium text-neutral-600 hover:text-primary-600 transition-colors ml-auto"
            >
              <Filter className="w-3.5 h-3.5" />
              {showFilters ? 'Hide Advanced Filters' : 'Show Advanced Filters'}
            </button>
          </div>

          {showFilters && (
          <>
          {/* Status Filter */}
          <Select
            label="Status"
            value={selectedStatus}
            onChange={(e) => {
              setSelectedStatus(e.target.value);
              setCurrentPage(1);
            }}
            options={[
              { value: 'all', label: 'All Status' },
              { value: 'draft', label: 'Draft' },
              { value: 'pending_requisition', label: 'Pending Requisition' },
              { value: 'signed_requisition_uploaded', label: 'Signed Uploaded' },
              { value: 'approved', label: 'Approved' },
              { value: 'dispatched', label: 'Dispatched' },
              { value: 'delivered', label: 'Delivered' },
              { value: 'closed', label: 'Closed' },
              { value: 'cancelled', label: 'Cancelled' },
            ]}
          />

          {/* Date Range Filter */}
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-2">Date Range</label>
            <div className="flex flex-wrap gap-1.5 mb-3">
              {[
                { label: 'Today', value: 'today' as const },
                { label: 'This Week', value: 'this_week' as const },
                { label: 'This Month', value: 'this_month' as const },
                { label: 'Last Month', value: 'last_month' as const },
                { label: 'This FY', value: 'this_fy' as const },
              ].map((opt) => (
                <FilterPill
                  key={opt.value}
                  onClick={() => {
                    const range = getDateRange(opt.value);
                    setDateFrom(range.from);
                    setDateTo(range.to);
                    setCurrentPage(1);
                  }}
                >
                  {opt.label}
                </FilterPill>
              ))}
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <DateInput label="From Date" value={dateFrom} onChange={(e) => { setDateFrom(e.target.value); setCurrentPage(1); }} />
              <DateInput label="To Date" value={dateTo} onChange={(e) => { setDateTo(e.target.value); setCurrentPage(1); }} />
          </div>
        </div>
          </>)}
        </div>
      </Card>

      {/* Orders List */}
      {isLoading ? (
        <ListLoadingState message="Loading orders..." />
      ) : items.length === 0 ? (
        <ListEmptyState message="No orders found" />
      ) : (
        <div className="space-y-3">
          {items.map((order) => (
            <Card
              key={order.id}
              padding="lg"
              className="cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => navigate(`/orders/${order.id}`)}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-4">
                    <div>
                      <h3 className="font-semibold text-neutral-900">{order.order_number}</h3>
                      <p className="text-sm text-neutral-500 mt-1">
                        {order.vendor?.name || 'Unknown Vendor'}
                      </p>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-4 text-right">
                  <div>
                    <p className="text-sm font-medium text-neutral-700">
                      {order.items?.length || 0} items
                    </p>
                    <p className="text-xs text-neutral-500 mt-1">
                      {formatDate(order.created_at)}
                    </p>
                  </div>
                  <StatusBadge status={order.status}>{formatStatus(order.status)}</StatusBadge>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && !isLoading && (
        <Card padding="lg">
          <div className="flex items-center justify-between">
            <p className="text-sm text-neutral-600">
              Page {currentPage} of {totalPages} ({totalItems} total orders)
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
