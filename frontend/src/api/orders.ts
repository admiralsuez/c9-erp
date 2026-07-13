import { apiClient } from './client';

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface OrderItemResponse {
  id: number;
  order_id: number;
  item_id: number;
  quantity_ordered: number;
  quantity_reserved: number;
  quantity_dispatched: number;
}

export interface OrderTimelineEntry {
  id: number;
  order_id: number;
  action: string;
  comments?: string;
  user_id: number;
  created_at: string;
}

export interface OrderResponse {
  id: number;
  order_number: string;
  vendor_id: number;
  vendor?: {
    id: number;
    name: string;
  };
  status: string;
  remarks?: string;
  delivery_address?: string;
  created_by?: number;
  created_at: string;
  updated_at: string;
  items: OrderItemResponse[];
  timeline_entries?: OrderTimelineEntry[];
}

export interface DispatchItemRequest {
  item_id: number;
  quantity: number;
}

export interface DispatchRequestBody {
  items: DispatchItemRequest[];
  partial?: boolean;
}

export interface OrderItemRequest {
  item_id: number;
  quantity_ordered: number;
}

export interface OrderCreateRequest {
  vendor_id: number;
  items: OrderItemRequest[];
  remarks?: string;
  delivery_address?: string;
}

export interface OrderUpdateRequest {
  vendor_id?: number;
  items?: OrderItemRequest[];
  remarks?: string;
  delivery_address?: string;
}

export const ordersApi = {
  list: async (
    page: number = 1,
    size: number = 20,
    status?: string,
    search?: string,
    date_from?: string,
    date_to?: string,
    sort_by?: string,
    status_not?: string
  ): Promise<PaginatedResponse<OrderResponse>> => {
    const params = new URLSearchParams();
    params.append('page', page.toString());
    params.append('size', size.toString());
    if (status) {
      params.append('status', status);
    }
    if (status_not) {
      params.append('status_not', status_not);
    }
    if (search) {
      params.append('search', search);
    }
    if (date_from) {
      params.append('date_from', date_from);
    }
    if (date_to) {
      params.append('date_to', date_to);
    }
    if (sort_by) {
      params.append('sort_by', sort_by);
    }
    const response = await apiClient.get<PaginatedResponse<OrderResponse>>(
      `/orders?${params.toString()}`
    );
    return response.data;
  },

  get: async (orderId: number): Promise<OrderResponse> => {
    const response = await apiClient.get<OrderResponse>(`/orders/${orderId}`);
    return response.data;
  },

  create: async (data: OrderCreateRequest): Promise<OrderResponse> => {
    const response = await apiClient.post<OrderResponse>('/orders', data);
    return response.data;
  },

  update: async (
    orderId: number,
    data: OrderUpdateRequest
  ): Promise<OrderResponse> => {
    const response = await apiClient.patch<OrderResponse>(
      `/orders/${orderId}`,
      data
    );
    return response.data;
  },

  submitRequisition: async (orderId: number, approverId?: number): Promise<OrderResponse> => {
    const response = await apiClient.post<OrderResponse>(
      `/orders/${orderId}/submit-requisition?approver_id=${approverId}`
    );
    return response.data;
  },

  uploadSigned: async (orderId: number, file: File): Promise<OrderResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post<OrderResponse>(
      `/orders/${orderId}/upload-signed`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return response.data;
  },

  approve: async (orderId: number): Promise<OrderResponse> => {
    const response = await apiClient.post<OrderResponse>(`/orders/${orderId}/approve`);
    return response.data;
  },

  approveWithSignature: async (orderId: number, signatureData: string): Promise<OrderResponse> => {
    const response = await apiClient.post<OrderResponse>(
      `/orders/${orderId}/approve-with-signature?signature_data=${encodeURIComponent(signatureData)}`
    );
    return response.data;
  },

  dispatch: async (orderId: number, data: DispatchRequestBody): Promise<OrderResponse> => {
    const response = await apiClient.post<OrderResponse>(`/orders/${orderId}/dispatch`, data);
    return response.data;
  },

  deliver: async (orderId: number): Promise<OrderResponse> => {
    const response = await apiClient.post<OrderResponse>(`/orders/${orderId}/deliver`);
    return response.data;
  },

  close: async (orderId: number): Promise<OrderResponse> => {
    const response = await apiClient.post<OrderResponse>(`/orders/${orderId}/close`);
    return response.data;
  },

  cancel: async (orderId: number): Promise<OrderResponse> => {
    const response = await apiClient.post<OrderResponse>(`/orders/${orderId}/cancel`);
    return response.data;
  },
};
