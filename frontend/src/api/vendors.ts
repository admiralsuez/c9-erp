import { apiClient } from './client';

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface VendorType {
  id: number;
  name: string;
}

export interface VendorResponse {
  id: number;
  name: string;
  vendor_type: string;
  vendor_type_id?: number | null;
  contact_person: string;
  phone: string;
  email: string;
  address: string;
  city: string;
  state: string;
  pincode?: string;
  gst: string;
  notes: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  parent_id?: number | null;
  children?: VendorResponse[];
}

export interface VendorCreateRequest {
  name: string;
  vendor_type?: string;
  vendor_type_id?: number | null;
  contact_person?: string;
  phone?: string;
  email?: string;
  address?: string;
  city?: string;
  state?: string;
  pincode?: string;
  gst?: string;
  notes?: string;
  parent_id?: number | null;
}

export const vendorApi = {
  list: async (
    page: number = 1,
    size: number = 20,
    search?: string,
    vendorType?: string,
    city?: string,
    sortBy: string = 'last_added'
  ): Promise<PaginatedResponse<VendorResponse>> => {
    const params = new URLSearchParams();
    params.append('page', page.toString());
    params.append('size', size.toString());
    if (search) {
      params.append('search', search);
    }
    if (vendorType) {
      params.append('vendor_type', vendorType);
    }
    if (city) {
      params.append('city', city);
    }
    params.append('sort_by', sortBy);
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

  listTypes: async (): Promise<VendorType[]> => {
    const response = await apiClient.get<VendorType[]>('/vendors/types');
    return response.data;
  },

  createType: async (data: { name: string }): Promise<VendorType> => {
    const response = await apiClient.post<VendorType>('/vendors/types', data);
    return response.data;
  },

  types: {
    list: async (): Promise<VendorType[]> => {
      const response = await apiClient.get<VendorType[]>('/vendors/types');
      return response.data;
    },

    create: async (name: string): Promise<VendorType> => {
      const response = await apiClient.post<VendorType>('/vendors/types', { name });
      return response.data;
    }
  }
};
