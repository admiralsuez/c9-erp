import React, { useState } from 'react';
import { Card } from './ui';
import { MapPin, Plus } from 'lucide-react';
import type { VendorResponse } from '../api/vendors';

interface VendorAddressSelectorProps {
  vendor: VendorResponse | null;
  selectedAddressId: number | null;
  onAddressSelect: (addressId: number | null) => void;
  customAddress: string;
  onCustomAddressChange: (address: string) => void;
}

/**
 * Vendor Address Selector Component
 * 
 * Allows users to select from a vendor's multiple addresses or enter a custom address.
 * Displays the vendor's primary address and any child addresses (alternate locations).
 */
export const VendorAddressSelector: React.FC<VendorAddressSelectorProps> = ({
  vendor,
  selectedAddressId,
  onAddressSelect,
  customAddress,
  onCustomAddressChange,
}) => {
  const [showCustomAddress, setShowCustomAddress] = useState(false);

  if (!vendor) {
    return null;
  }

  // Get all addresses: primary vendor + children
  const addresses = [
    {
      id: vendor.id,
      name: `${vendor.name} (Primary)`,
      address: vendor.address || 'No address provided',
      city: vendor.city || '',
      state: vendor.state || '',
      pincode: vendor.pincode || '',
      is_primary: true,
    },
    ...(vendor.children ? vendor.children.map((child: VendorResponse, idx: number) => ({
      id: child.id,
      name: `${child.name} (Address ${idx + 2})`,
      address: child.address || 'No address provided',
      city: child.city || '',
      state: child.state || '',
      pincode: child.pincode || '',
      is_primary: false,
    })) : []),
  ];

  const hasMultipleAddresses = addresses.length > 1;

  return (
    <Card padding="lg" className="border border-neutral-200">
      <h3 className="text-sm font-semibold text-neutral-900 mb-4 flex items-center gap-2">
        <MapPin className="w-4 h-4" />
        Delivery Address
      </h3>

      {/* Address Selector */}
      <div className="space-y-3 mb-4">
        {addresses.map((addr) => (
          <label
            key={addr.id}
            className="flex items-start gap-3 p-3 border border-neutral-200 rounded-lg hover:bg-neutral-50 cursor-pointer"
          >
            <input
              type="radio"
              name="address"
              value={addr.id}
              checked={selectedAddressId === addr.id && !showCustomAddress}
              onChange={() => {
                onAddressSelect(addr.id);
                setShowCustomAddress(false);
              }}
              className="mt-1 w-4 h-4 text-primary-600 rounded border-neutral-300 focus:ring-2 focus:ring-primary-500"
            />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-neutral-900">{addr.name}</p>
              <p className="text-xs text-neutral-600 mt-1">
                {addr.address}
                {addr.city && `, ${addr.city}`}
                {addr.state && `, ${addr.state}`}
                {addr.pincode && ` - ${addr.pincode}`}
              </p>
            </div>
          </label>
        ))}

        {/* Custom Address Option */}
        <label className="flex items-start gap-3 p-3 border border-neutral-200 rounded-lg hover:bg-neutral-50 cursor-pointer">
          <input
            type="radio"
            name="address"
            value="custom"
            checked={showCustomAddress}
            onChange={() => {
              setShowCustomAddress(true);
              onAddressSelect(null);
            }}
            className="mt-1 w-4 h-4 text-primary-600 rounded border-neutral-300 focus:ring-2 focus:ring-primary-500"
          />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-neutral-900 flex items-center gap-2">
              <Plus className="w-4 h-4" />
              Enter Custom Address
            </p>
            <p className="text-xs text-neutral-500 mt-1">
              Enter a different delivery address
            </p>
          </div>
        </label>
      </div>

      {/* Custom Address Input */}
      {showCustomAddress && (
        <div className="border-t border-neutral-200 pt-4">
          <label className="block text-xs font-medium text-neutral-700 mb-2">
            Delivery Address
          </label>
          <textarea
            value={customAddress}
            onChange={(e) => onCustomAddressChange(e.target.value)}
            placeholder="Enter complete delivery address..."
            rows={3}
            className="w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
      )}

      {/* Info */}
      {hasMultipleAddresses && (
        <div className="mt-3 p-2 bg-blue-50 border border-blue-200 rounded text-xs text-blue-700">
          This vendor has {addresses.length} addresses available. Select or customize as needed.
        </div>
      )}
    </Card>
  );
};
