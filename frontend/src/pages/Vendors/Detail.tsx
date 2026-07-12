import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Card, Button, ListLoadingState } from '../../components/ui';
import { cardErrorPadded, formLabel } from '../../styles/classNames';
import { ArrowLeft, Edit2, Trash2, Loader, AlertCircle } from 'lucide-react';
import { useVendor, useUpdateVendor, useDeleteVendor } from '../../hooks/useVendors';
import { formatDate } from '../../utils/format';
import type { VendorCreateRequest } from '../../api/vendors';

export const VendorDetailPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const vendorId = id ? parseInt(id) : null;

  const [isEditMode, setIsEditMode] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const [formError, setFormError] = useState('');

  // Form state for editing
  const [formData, setFormData] = useState<VendorCreateRequest>({
    name: '',
    vendor_type: '',
    contact_person: '',
    phone: '',
    email: '',
    address: '',
    city: '',
    state: '',
    gst: '',
    notes: '',
  });

  const { data: vendor, isLoading, error } = useVendor(vendorId);
  const { mutate: updateVendor, isPending: isUpdating } = useUpdateVendor();
  const { mutate: deleteVendor, isPending: isDeleting } = useDeleteVendor();

  // Populate form when vendor data loads
  React.useEffect(() => {
    if (vendor) {
      setFormData({
        name: vendor.name,
        vendor_type: vendor.vendor_type,
        contact_person: vendor.contact_person || '',
        phone: vendor.phone || '',
        email: vendor.email || '',
        address: vendor.address || '',
        city: vendor.city || '',
        state: vendor.state || '',
        gst: vendor.gst || '',
        notes: vendor.notes || '',
      });
    }
  }, [vendor]);

  const handleUpdate = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');

    if (!formData.name || !formData.vendor_type) {
      setFormError('Name and Vendor Type are required');
      return;
    }

    if (!vendorId) return;

    updateVendor(
      { vendorId, data: formData },
      {
        onSuccess: () => {
          setIsEditMode(false);
        },
        onError: (error: any) => {
          setFormError(
            error?.response?.data?.detail ||
            error?.message ||
            'Failed to update vendor'
          );
        },
      }
    );
  };

  const handleDelete = () => {
    if (!vendorId) return;

    deleteVendor(vendorId, {
      onSuccess: () => {
        navigate('/vendors');
      },
      onError: (error: any) => {
        setFormError(
          error?.response?.data?.detail ||
          error?.message ||
          'Failed to delete vendor'
        );
        setDeleteConfirm(false);
      },
    });
  };

  if (isLoading) return <ListLoadingState message="Loading vendor..." />;

  if (error || !vendor) {
    return (
      <div className="space-y-6 pb-6">
        <button
          onClick={() => navigate('/vendors')}
          className="p-2 hover:bg-neutral-100 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5 text-neutral-600" />
        </button>
        <Card className={cardErrorPadded} padding="lg">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-error flex-shrink-0" />
            <p className="text-error">
              {error instanceof Error ? error.message : 'Vendor not found'}
            </p>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/vendors')}
            className="p-2 hover:bg-neutral-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-neutral-600" />
          </button>
          <div>
            <h1 className="text-3xl font-bold text-neutral-900">{vendor.name}</h1>
            <p className="text-neutral-600 mt-1">{vendor.vendor_type}</p>
          </div>
        </div>

        {!isEditMode && (
          <div className="flex gap-2">
            <Button
              onClick={() => setIsEditMode(true)}
              className="flex items-center gap-2 bg-primary-600 text-white hover:bg-primary-700"
            >
              <Edit2 className="w-4 h-4" />
              Edit
            </Button>
            <Button
              onClick={() => setDeleteConfirm(true)}
              className="flex items-center gap-2 bg-error/10 text-error hover:bg-error/20"
            >
              <Trash2 className="w-4 h-4" />
              Delete
            </Button>
          </div>
        )}
      </div>

      {/* Error Banner */}
      {formError && (
        <Card className={cardErrorPadded} padding="lg">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-error flex-shrink-0" />
            <p className="text-error">{formError}</p>
          </div>
        </Card>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <Card className="border border-error bg-error/5 p-6" padding="lg">
          <h3 className="text-lg font-semibold text-neutral-900 mb-2">
            Delete Vendor?
          </h3>
          <p className="text-neutral-600 mb-4">
            This action cannot be undone. Are you sure you want to delete{' '}
            <strong>{vendor.name}</strong>?
          </p>
          <div className="flex gap-3 justify-end">
            <Button
              onClick={() => setDeleteConfirm(false)}
              disabled={isDeleting}
              className="px-4 py-2 border border-neutral-300 rounded-lg text-neutral-700 hover:bg-neutral-50"
            >
              Cancel
            </Button>
            <Button
              onClick={handleDelete}
              disabled={isDeleting}
              className="px-4 py-2 bg-error text-white hover:bg-error-dark disabled:opacity-50 flex items-center gap-2"
            >
              {isDeleting && <Loader className="w-4 h-4 animate-spin" />}
              {isDeleting ? 'Deleting...' : 'Delete'}
            </Button>
          </div>
        </Card>
      )}

      {/* View/Edit Mode */}
      {!isEditMode ? (
        // VIEW MODE
        <>
          {/* Contact Information */}
          <Card padding="lg">
            <h2 className="text-lg font-semibold text-neutral-900 mb-4">
              Contact Information
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <p className="text-sm text-neutral-600 font-medium mb-1">
                  Contact Person
                </p>
                <p className="text-neutral-900">{vendor.contact_person || '—'}</p>
              </div>
              <div>
                <p className="text-sm text-neutral-600 font-medium mb-1">Phone</p>
                <p className="text-neutral-900">{vendor.phone || '—'}</p>
              </div>
              <div className="md:col-span-2">
                <p className="text-sm text-neutral-600 font-medium mb-1">Email</p>
                <p className="text-neutral-900">{vendor.email || '—'}</p>
              </div>
            </div>
          </Card>

          {/* Address Information */}
          <Card padding="lg">
            <h2 className="text-lg font-semibold text-neutral-900 mb-4">
              Address
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="md:col-span-2">
                <p className="text-sm text-neutral-600 font-medium mb-1">
                  Address
                </p>
                <p className="text-neutral-900">{vendor.address || '—'}</p>
              </div>
              <div>
                <p className="text-sm text-neutral-600 font-medium mb-1">City</p>
                <p className="text-neutral-900">{vendor.city || '—'}</p>
              </div>
              <div>
                <p className="text-sm text-neutral-600 font-medium mb-1">State</p>
                <p className="text-neutral-900">{vendor.state || '—'}</p>
              </div>
            </div>
          </Card>

          {/* Tax Information */}
          <Card padding="lg">
            <h2 className="text-lg font-semibold text-neutral-900 mb-4">
              Tax Information
            </h2>
            <div>
              <p className="text-sm text-neutral-600 font-medium mb-1">GST Number</p>
              <p className="text-neutral-900 font-mono">{vendor.gst || '—'}</p>
            </div>
          </Card>

          {/* Additional Information */}
          {vendor.notes && (
            <Card padding="lg">
              <h2 className="text-lg font-semibold text-neutral-900 mb-4">Notes</h2>
              <p className="text-neutral-900">{vendor.notes}</p>
            </Card>
          )}

          {/* Metadata */}
          <Card padding="lg">
            <h2 className="text-lg font-semibold text-neutral-900 mb-4">
              Metadata
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <p className="text-sm text-neutral-600 font-medium mb-1">
                  Status
                </p>
                <span
                  className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold ${
                    vendor.is_active ? 'bg-success/10 text-success' : 'bg-neutral-100 text-neutral-700'
                  }`}
                >
                  {vendor.is_active ? 'ACTIVE' : 'INACTIVE'}
                </span>
              </div>
              <div>
                <p className="text-sm text-neutral-600 font-medium mb-1">
                  Created
                </p>
                <p className="text-neutral-900">
                  {formatDate(vendor.created_at)}
                </p>
              </div>
              <div>
                <p className="text-sm text-neutral-600 font-medium mb-1">
                  Last Updated
                </p>
                <p className="text-neutral-900">
                  {formatDate(vendor.updated_at)}
                </p>
              </div>
            </div>
          </Card>
        </>
      ) : (
        // EDIT MODE
        <Card padding="lg">
          <h2 className="text-lg font-semibold text-neutral-900 mb-4">Edit Vendor</h2>
          <form onSubmit={handleUpdate} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className={formLabel}>
                  Vendor Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  disabled={isUpdating}
                />
              </div>
              <div>
                <label className={formLabel}>
                  Vendor Type *
                </label>
                <input
                  type="text"
                  value={formData.vendor_type}
                  onChange={(e) =>
                    setFormData({ ...formData, vendor_type: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  disabled={isUpdating}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className={formLabel}>
                  Contact Person
                </label>
                <input
                  type="text"
                  value={formData.contact_person}
                  onChange={(e) =>
                    setFormData({ ...formData, contact_person: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  disabled={isUpdating}
                />
              </div>
              <div>
                <label className={formLabel}>
                  Phone
                </label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) =>
                    setFormData({ ...formData, phone: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  disabled={isUpdating}
                />
              </div>
            </div>

            <div>
              <label className={formLabel}>
                Email
              </label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) =>
                  setFormData({ ...formData, email: e.target.value })
                }
                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                disabled={isUpdating}
              />
            </div>

            <div>
              <label className={formLabel}>
                Address
              </label>
              <textarea
                value={formData.address}
                onChange={(e) =>
                  setFormData({ ...formData, address: e.target.value })
                }
                rows={2}
                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                disabled={isUpdating}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className={formLabel}>
                  City
                </label>
                <input
                  type="text"
                  value={formData.city}
                  onChange={(e) =>
                    setFormData({ ...formData, city: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  disabled={isUpdating}
                />
              </div>
              <div>
                <label className={formLabel}>
                  State
                </label>
                <input
                  type="text"
                  value={formData.state}
                  onChange={(e) =>
                    setFormData({ ...formData, state: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  disabled={isUpdating}
                />
              </div>
            </div>

            <div>
              <label className={formLabel}>
                GST Number
              </label>
              <input
                type="text"
                value={formData.gst}
                onChange={(e) =>
                  setFormData({ ...formData, gst: e.target.value })
                }
                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                disabled={isUpdating}
              />
            </div>

            <div>
              <label className={formLabel}>
                Notes
              </label>
              <textarea
                value={formData.notes}
                onChange={(e) =>
                  setFormData({ ...formData, notes: e.target.value })
                }
                rows={3}
                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                disabled={isUpdating}
              />
            </div>

            <div className="flex gap-3 justify-end">
              <Button
                type="button"
                onClick={() => setIsEditMode(false)}
                disabled={isUpdating}
                className="px-6 py-2 border border-neutral-300 rounded-lg text-neutral-700 hover:bg-neutral-50"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={isUpdating}
                className="px-6 py-2 bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50 flex items-center gap-2"
              >
                {isUpdating && <Loader className="w-4 h-4 animate-spin" />}
                {isUpdating ? 'Saving...' : 'Save Changes'}
              </Button>
            </div>
          </form>
        </Card>
      )}
    </div>
  );
};

export default VendorDetailPage;
