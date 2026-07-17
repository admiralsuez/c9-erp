import { apiClient } from './client';

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface VendorResponse {
  id: number;
  name: string;
  vendor_type: string;
  contact_person: string;
  phone: string;
  email: string;
  address: string;
  city: string;
  state: string;
  pincode: string;
  gst: string;
  notes: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface VendorCreateRequest {
  name: string;
  vendor_type: string;
  contact_person?: string;
  phone?: string;
  email?: string;
  address?: string;
  city?: string;
  state?: string;
  pincode?: string;
  gst?: string;
  notes?: string;
}

export const vendorApi = {
  list: async (
    page: number = 1,
    size: number = 20,
    search?: string
  ): Promise<PaginatedResponse<VendorResponse>> => {
    const params = new URLSearchParams();
    params.append('page', page.toString());
    params.append('size', size.toString());
    if (search) {
      params.append('search', search);
    }
    const response = await apiClient.get<PaginatedResponse<VendorResponse>>(
      `/vendors?${params.toString()}`
    );
    return response.data;
  },

  get: async (vendorId: number): Promise<VendorResponse> => {
    const response = await apiClient.get<VendorResponse>(`/vendors/${vendorId}`);
    return response.data;
  },

  create: async (data: VendorCreateRequest): Promise<VendorResponse> => {
    const response = await apiClient.post<VendorResponse>('/vendors', data);
    return response.data;
  },

  update: async (
    vendorId: number,
    data: Partial<VendorCreateRequest>
  ): Promise<VendorResponse> => {
    const response = await apiClient.patch<VendorResponse>(
      `/vendors/${vendorId}`,
      data
    );
    return response.data;
  },

  delete: async (vendorId: number): Promise<void> => {
    await apiClient.delete(`/vendors/${vendorId}`);
  },
};
