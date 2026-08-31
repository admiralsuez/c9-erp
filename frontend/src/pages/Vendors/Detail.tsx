import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Card, Button, ListLoadingState } from '../../components/ui';
import { cardErrorPadded, formLabel } from '../../styles/classNames';
import { ArrowLeft, Edit2, Trash2, Loader, AlertCircle, Plus, MapPin } from 'lucide-react';
import { useVendor, useUpdateVendor, useDeleteVendor, useCreateVendor } from '../../hooks/useVendors';
import { vendorApi } from '../../api/vendors';
import type { VendorCreateRequest } from '../../api/vendors';
import { formatDate } from '../../utils/format';

export const VendorDetailPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const vendorId = id ? parseInt(id) : null;

  const [isEditMode, setIsEditMode] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const [formError, setFormError] = useState('');
  const [showAddressForm, setShowAddressForm] = useState(false);
  const [newAddress, setNewAddress] = useState({ address: '', city: '', state: '', pincode: '' });

  // Form state for editing
  const [formData, setFormData] = useState<VendorCreateRequest>({
    name: '',
    vendor_type_id: null,
    contact_person: '',
    phone: '',
    email: '',
    address: '',
    city: '',
    state: '',
    gst: '',
    notes: '',
  });
  const [vendorTypes, setVendorTypes] = useState<any[]>([]);

  const { data: vendor, isLoading, error } = useVendor(vendorId);
  const { mutate: updateVendor, isPending: isUpdating } = useUpdateVendor();
  const { mutate: deleteVendor, isPending: isDeleting } = useDeleteVendor();
  const { mutate: createChild, isPending: isCreatingChild } = useCreateVendor();

  // Populate form when vendor data loads
  React.useEffect(() => {
    if (vendor) {
      setFormData({
        name: vendor.name,
        vendor_type_id: vendor.vendor_type_id || null,
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

  // Load vendor types on mount
  React.useEffect(() => {
    const loadTypes = async () => {
      try {
        const types = await vendorApi.types.list();
        setVendorTypes(types);
      } catch (err) {
        console.error('Failed to load vendor types:', err);
      }
    };
    loadTypes();
  }, []);

  const addAddress = () => {
    if (!vendorId) return;
    if (!newAddress.address.trim()) {
      setFormError('Address is required');
      return;
    }
    createChild(
      {
        name: `${formData.name} - Address ${(vendor?.children?.length ?? 0) + 2}`,
        vendor_type_id: formData.vendor_type_id,
        address: newAddress.address,
        city: newAddress.city,
        state: newAddress.state,
        pincode: newAddress.pincode,
        parent_id: vendorId,
      },
      {
        onSuccess: () => {
          setNewAddress({ address: '', city: '', state: '', pincode: '' });
          setShowAddressForm(false);
          setFormError('');
        },
        onError: (error: any) => {
          setFormError(
            error?.response?.data?.detail ||
            error?.message ||
            'Failed to add address'
          );
        },
      }
    );
  };

  const removeAddress = (childId: number) => {
    if (!childId) return;
    deleteVendor(childId, {
      onError: (error: any) => {
        setFormError(
          error?.response?.data?.detail ||
          error?.message ||
          'Failed to remove address'
        );
      },
    });
  };

  const handleUpdate = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');

    if (!formData.name || !formData.vendor_type_id) {
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

            {/* Additional Delivery Addresses (view mode) */}
            {vendor.children && vendor.children.length > 0 && (
              <div className="mt-6 pt-6 border-t border-neutral-200">
                <h3 className="text-sm font-semibold text-neutral-900 mb-3 flex items-center gap-2">
                  <MapPin className="w-4 h-4" />
                  Additional Delivery Addresses
                </h3>
                <div className="space-y-2">
                  {vendor.children.map((child) => (
                    <div key={child.id} className="p-3 bg-neutral-50 border border-neutral-200 rounded-lg">
                      <p className="text-sm font-medium text-neutral-900">{child.name}</p>
                      <p className="text-xs text-neutral-600 mt-0.5">
                        {child.address || '—'}
                        {child.city && `, ${child.city}`}
                        {child.state && `, ${child.state}`}
                        {child.pincode && ` - ${child.pincode}`}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
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
                <select
                  value={formData.vendor_type_id ?? ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      vendor_type_id: e.target.value ? parseInt(e.target.value) : null,
                    })
                  }
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
                  disabled={isUpdating}
                >
                  <option value="">Select a vendor type...</option>
                  {vendorTypes.map((type) => (
                    <option key={type.id} value={type.id}>
                      {type.name}
                    </option>
                  ))}
                </select>
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

            {/* Additional Delivery Addresses (edit mode) */}
            <div className="border-t border-neutral-200 pt-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-neutral-900 flex items-center gap-2">
                  <MapPin className="w-4 h-4" />
                  Additional Delivery Addresses
                  <span className="text-xs font-normal text-neutral-500">({vendor.children?.length ?? 0}/20)</span>
                </h3>
                {!showAddressForm && (vendor.children?.length ?? 0) < 20 && (
                  <button
                    type="button"
                    onClick={() => setShowAddressForm(true)}
                    className="flex items-center gap-1 text-sm text-primary-600 hover:text-primary-700"
                  >
                    <Plus className="w-4 h-4" />
                    Add Address
                  </button>
                )}
              </div>

              {/* Add Address Form */}
              {showAddressForm && (
                <div className="p-4 bg-neutral-50 border border-neutral-200 rounded-lg mb-4 space-y-3">
                  <div>
                    <label className="block text-xs font-medium text-neutral-700 mb-1">Address</label>
                    <textarea
                      value={newAddress.address}
                      onChange={(e) => setNewAddress({ ...newAddress, address: e.target.value })}
                      rows={2}
                      className="w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                      disabled={isCreatingChild}
                    />
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div>
                      <label className="block text-xs font-medium text-neutral-700 mb-1">City</label>
                      <input
                        type="text"
                        value={newAddress.city}
                        onChange={(e) => setNewAddress({ ...newAddress, city: e.target.value })}
                        className="w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                        disabled={isCreatingChild}
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-neutral-700 mb-1">State</label>
                      <input
                        type="text"
                        value={newAddress.state}
                        onChange={(e) => setNewAddress({ ...newAddress, state: e.target.value })}
                        className="w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                        disabled={isCreatingChild}
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-neutral-700 mb-1">Pincode</label>
                      <input
                        type="text"
                        value={newAddress.pincode}
                        onChange={(e) => setNewAddress({ ...newAddress, pincode: e.target.value })}
                        className="w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                        disabled={isCreatingChild}
                      />
                    </div>
                  </div>
                  <div className="flex gap-2 justify-end">
                    <button
                      type="button"
                      onClick={() => {
                        setShowAddressForm(false);
                        setNewAddress({ address: '', city: '', state: '', pincode: '' });
                      }}
                      className="px-3 py-1.5 text-sm border border-neutral-300 rounded text-neutral-700 hover:bg-neutral-100"
                      disabled={isCreatingChild}
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={addAddress}
                      disabled={isCreatingChild || !newAddress.address.trim()}
                      className="px-3 py-1.5 text-sm bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50 flex items-center gap-1"
                    >
                      {isCreatingChild && <Loader className="w-3.5 h-3.5 animate-spin" />}
                      {isCreatingChild ? 'Adding...' : 'Add Address'}
                    </button>
                  </div>
                </div>
              )}

              {/* Existing Addresses List */}
              {vendor.children && vendor.children.length > 0 ? (
                <div className="space-y-2">
                  {vendor.children.map((child) => (
                    <div key={child.id} className="flex items-start justify-between p-3 bg-neutral-50 border border-neutral-200 rounded-lg">
                      <div className="flex-1">
                        <p className="text-sm font-medium text-neutral-900">{child.name}</p>
                        <p className="text-xs text-neutral-600 mt-0.5">
                          {child.address || '—'}
                          {child.city && `, ${child.city}`}
                          {child.state && `, ${child.state}`}
                          {child.pincode && ` - ${child.pincode}`}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => removeAddress(child.id)}
                        disabled={isDeleting}
                        className="p-1 text-error hover:bg-error/10 rounded transition-colors ml-2"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-neutral-500 text-sm text-center py-2">No additional delivery addresses added yet</p>
              )}
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
