import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Button } from '../../components/ui';
import { cardErrorPadded, formLabel } from '../../styles/classNames';
import { ArrowLeft, Loader, AlertCircle, Plus, Trash2, MapPin } from 'lucide-react';
import { useCreateVendor } from '../../hooks/useVendors';
import type { VendorCreateRequest } from '../../api/vendors';

interface AddressEntry {
  id: string;
  address: string;
  city: string;
  state: string;
  pincode: string;
  is_primary: boolean;
}

export const VendorFormPage: React.FC = () => {
  const navigate = useNavigate();
  const [formError, setFormError] = useState('');
  const [addresses, setAddresses] = useState<AddressEntry[]>([
    { id: '0', address: '', city: '', state: '', pincode: '', is_primary: true }
  ]);
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
  const [showAddressForm, setShowAddressForm] = useState(false);
  const [newAddress, setNewAddress] = useState<Omit<AddressEntry, 'id'> & { id?: string }>({
    address: '',
    city: '',
    state: '',
    pincode: '',
    is_primary: false
  });

  const { mutate: createVendor, isPending } = useCreateVendor((vendor) => {
    navigate(`/vendors/${vendor.id}`);
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');

    if (!formData.name || !formData.vendor_type) {
      setFormError('Name and Vendor Type are required');
      return;
    }

    createVendor(formData);
  };

  return (
    <div className="space-y-6 pb-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/vendors')}
          className="p-2 hover:bg-neutral-100 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5 text-neutral-600" />
        </button>
        <div>
          <h1 className="text-3xl font-bold text-neutral-900">Add New Vendor</h1>
          <p className="text-neutral-600 mt-1">
            Enter vendor details and contact information
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Error Banner */}
        {formError && (
          <Card className={cardErrorPadded} padding="lg">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-error flex-shrink-0" />
              <p className="text-error">{formError}</p>
            </div>
          </Card>
        )}

        {/* Section 1: Vendor Identity */}
        <Card padding="lg">
          <h2 className="text-lg font-semibold text-neutral-900 mb-4">
            Vendor Identity
          </h2>
          <div className="space-y-4">
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
                  placeholder="e.g., ABC Traders"
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  disabled={isPending}
                  required
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
                  placeholder="e.g., Supplier, Wholesale, Distributor"
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  disabled={isPending}
                  required
                />
              </div>
            </div>
          </div>
        </Card>

        {/* Section 2: Contact Information */}
        <Card padding="lg">
          <h2 className="text-lg font-semibold text-neutral-900 mb-4">
            Contact Information
          </h2>
          <div className="space-y-4">
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
                  placeholder="e.g., John Smith"
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  disabled={isPending}
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
                  placeholder="e.g., +91-9876-543210"
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  disabled={isPending}
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
                placeholder="e.g., contact@vendor.com"
                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                disabled={isPending}
              />
            </div>
          </div>
        </Card>

        {/* Section 3: Primary Address */}
        <Card padding="lg">
          <h2 className="text-lg font-semibold text-neutral-900 mb-4 flex items-center gap-2">
            <MapPin className="w-5 h-5" />
            Primary Address
          </h2>
          <div className="space-y-4">
            <div>
              <label className={formLabel}>
                Address
              </label>
              <textarea
                value={formData.address}
                onChange={(e) =>
                  setFormData({ ...formData, address: e.target.value })
                }
                placeholder="e.g., 123 Business Street, Suite 100"
                rows={2}
                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                disabled={isPending}
              />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
                  placeholder="e.g., Mumbai"
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  disabled={isPending}
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
                  placeholder="e.g., Maharashtra"
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  disabled={isPending}
                />
              </div>
              <div>
                <label className={formLabel}>
                  Pincode
                </label>
                <input
                  type="text"
                  value={formData.pincode || ''}
                  onChange={(e) =>
                    setFormData({ ...formData, pincode: e.target.value })
                  }
                  placeholder="e.g., 400001"
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  disabled={isPending}
                />
              </div>
            </div>
          </div>
        </Card>

        {/* Section 3b: Additional Addresses */}
        <Card padding="lg">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-neutral-900 flex items-center gap-2">
              <MapPin className="w-5 h-5" />
              Additional Delivery Addresses
              <span className="text-sm font-normal text-neutral-500">({addresses.length - 1}/20)</span>
            </h2>
            {!showAddressForm && addresses.length < 21 && (
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

          {/* Address Add Form */}
          {showAddressForm && (
            <div className="p-4 bg-neutral-50 border border-neutral-200 rounded-lg mb-4 space-y-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-medium text-neutral-900">Add New Address</h4>
                <span className="text-xs text-neutral-500">{addresses.length - 1}/20</span>
              </div>
              <div>
                <label className="block text-xs font-medium text-neutral-700 mb-1">Address</label>
                <textarea
                  value={newAddress.address}
                  onChange={(e) => setNewAddress({ ...newAddress, address: e.target.value })}
                  placeholder="e.g., 456 Warehouse Road"
                  rows={2}
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                  disabled={isPending}
                />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-medium text-neutral-700 mb-1">City</label>
                  <input
                    type="text"
                    value={newAddress.city}
                    onChange={(e) => setNewAddress({ ...newAddress, city: e.target.value })}
                    placeholder="City"
                    className="w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                    disabled={isPending}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-neutral-700 mb-1">State</label>
                  <input
                    type="text"
                    value={newAddress.state}
                    onChange={(e) => setNewAddress({ ...newAddress, state: e.target.value })}
                    placeholder="State"
                    className="w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                    disabled={isPending}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-neutral-700 mb-1">Pincode</label>
                  <input
                    type="text"
                    value={newAddress.pincode}
                    onChange={(e) => setNewAddress({ ...newAddress, pincode: e.target.value })}
                    placeholder="Pincode"
                    className="w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                    disabled={isPending}
                  />
                </div>
              </div>
              <div className="flex gap-2 justify-end">
                <button
                  type="button"
                  onClick={() => {
                    setShowAddressForm(false);
                    setNewAddress({ address: '', city: '', state: '', pincode: '', is_primary: false });
                  }}
                  className="px-3 py-1.5 text-sm border border-neutral-300 rounded text-neutral-700 hover:bg-neutral-100"
                  disabled={isPending}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => {
                    if (newAddress.address.trim() && addresses.length < 21) {
                      setAddresses([...addresses, { ...newAddress, id: Date.now().toString() }]);
                      setNewAddress({ address: '', city: '', state: '', pincode: '', is_primary: false });
                      setShowAddressForm(false);
                    }
                  }}
                  className="px-3 py-1.5 text-sm bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50"
                  disabled={isPending || !newAddress.address.trim() || addresses.length >= 21}
                >
                  {addresses.length >= 21 ? 'Limit reached' : 'Add Address'}
                </button>
              </div>
            </div>
          )}

          {/* Addresses List */}
          {addresses.length > 0 ? (
            <div className="space-y-2">
              {addresses.map((addr) => (
                <div key={addr.id} className="flex items-start justify-between p-3 bg-neutral-50 border border-neutral-200 rounded-lg">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-neutral-900">{addr.address}</p>
                    <p className="text-xs text-neutral-600 mt-0.5">
                      {addr.city && `${addr.city}`}
                      {addr.state && `, ${addr.state}`}
                      {addr.pincode && ` - ${addr.pincode}`}
                    </p>
                  </div>
                  {!addr.is_primary && (
                    <button
                      type="button"
                      onClick={() => setAddresses(addresses.filter(a => a.id !== addr.id))}
                      className="p-1 text-error hover:bg-error/10 rounded transition-colors ml-2"
                      disabled={isPending}
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-neutral-500 text-sm text-center py-3">No additional addresses added yet</p>
          )}
        </Card>

        {/* Section 4: Tax Information */}
        <Card padding="lg">
          <h2 className="text-lg font-semibold text-neutral-900 mb-4">
            Tax Information
          </h2>
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
              placeholder="e.g., 27AAPFU0192F1Z5"
              className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              disabled={isPending}
            />
          </div>
        </Card>

        {/* Section 5: Additional Notes */}
        <Card padding="lg">
          <h2 className="text-lg font-semibold text-neutral-900 mb-4">
            Additional Information
          </h2>
          <div>
            <label className={formLabel}>
              Notes
            </label>
            <textarea
              value={formData.notes}
              onChange={(e) =>
                setFormData({ ...formData, notes: e.target.value })
              }
              placeholder="Add any special notes or remarks about this vendor..."
              rows={3}
              className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              disabled={isPending}
            />
          </div>
        </Card>

        {/* Submit Section */}
        <div className="flex gap-3 justify-end">
          <Button
            type="button"
            onClick={() => navigate('/vendors')}
            disabled={isPending}
            className="px-6 py-2 border border-neutral-300 rounded-lg text-neutral-700 hover:bg-neutral-50"
          >
            Cancel
          </Button>
          <Button
            type="submit"
            disabled={isPending}
            className="px-6 py-2 bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50 flex items-center gap-2"
          >
            {isPending && <Loader className="w-4 h-4 animate-spin" />}
            {isPending ? 'Creating...' : 'Create Vendor'}
          </Button>
        </div>
      </form>
    </div>
  );
};

export default VendorFormPage;
