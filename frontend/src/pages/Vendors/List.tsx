import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Button, TextInput, ListLoadingState, ListEmptyState, StatusBadge } from '../../components/ui';
import { Search, Plus, ChevronLeft, ChevronRight, AlertCircle } from 'lucide-react';
import { useVendors } from '../../hooks/useVendors';

const VENDORS_PER_PAGE = 20;

export const VendorsListPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);

  const { data, isLoading, error } = useVendors(
    currentPage,
    VENDORS_PER_PAGE,
    searchQuery || undefined
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
          <h1 className="text-3xl font-bold text-neutral-900">Vendors</h1>
          <p className="text-neutral-600 mt-1">Manage your supply partners ({totalItems} vendors)</p>
        </div>
        <Button
          onClick={() => navigate('/vendors/new')}
          className="flex items-center gap-2 bg-primary-600 text-white hover:bg-primary-700"
        >
          <Plus className="w-4 h-4" />
          Add Vendor
        </Button>
      </div>

      {error && (
        <Card className="bg-error/10 border border-error p-4" padding="lg">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-error flex-shrink-0" />
            <div>
              <p className="font-medium text-error">Failed to load vendors</p>
              <p className="text-sm text-error/80">
                {error instanceof Error ? error.message : 'An error occurred'}
              </p>
            </div>
          </div>
        </Card>
      )}

      <Card padding="lg">
        <TextInput
          icon={<Search className="w-4 h-4" />}
          placeholder="Search vendors by name, email, or phone..."
          value={searchQuery}
          onChange={(e) => {
            setSearchQuery(e.target.value);
            setCurrentPage(1);
          }}
        />
      </Card>

      {/* Vendors List */}
      {isLoading ? (
        <ListLoadingState message="Loading vendors..." />
      ) : items.length === 0 ? (
        <ListEmptyState message="No vendors found" />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {items.map((vendor) => (
            <Card
              key={vendor.id}
              padding="lg"
              className="cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => navigate(`/vendors/${vendor.id}`)}
            >
              <div className="space-y-4">
                <div>
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="text-lg font-semibold text-neutral-900">{vendor.name}</h3>
                    {vendor.vendor_type && (
                      <StatusBadge status={vendor.vendor_type}>{vendor.vendor_type}</StatusBadge>
                    )}
                  </div>
                  {vendor.contact_person && (
                    <p className="text-sm text-neutral-600">Contact: {vendor.contact_person}</p>
                  )}
                </div>

                <div className="space-y-2">
                  {vendor.email && (
                    <div className="flex items-center gap-2 text-sm">
                      <span className="text-neutral-500">Email:</span>
                      <a
                        href={`mailto:${vendor.email}`}
                        className="text-primary-600 hover:underline"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {vendor.email}
                      </a>
                    </div>
                  )}
                  {vendor.phone && (
                    <div className="flex items-center gap-2 text-sm">
                      <span className="text-neutral-500">Phone:</span>
                      <a
                        href={`tel:${vendor.phone}`}
                        className="text-primary-600 hover:underline"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {vendor.phone}
                      </a>
                    </div>
                  )}
                  {vendor.city && (
                    <div className="flex items-center gap-2 text-sm">
                      <span className="text-neutral-500">Location:</span>
                      <span>{vendor.city}</span>
                    </div>
                  )}
                </div>

                {vendor.is_active !== false && (
                  <div className="pt-2 border-t border-neutral-200">
                    <StatusBadge status="active">Active</StatusBadge>
                  </div>
                )}
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
              Page {currentPage} of {totalPages} ({totalItems} total vendors)
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
