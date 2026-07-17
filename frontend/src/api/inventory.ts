import { apiClient } from './client';

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface InventoryItemResponse {
  id: number;
  name: string;
  sku: string;
  barcode?: string;
  category_id?: number;
  item_type: string;
  current_quantity: number;
  reserved_quantity: number;
  minimum_quantity: number;
  bin_id?: number;
  description?: string;
  image_url?: string;
  parent_id?: number;
  children?: InventoryItemResponse[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
  deleted_at?: string;
}

export interface InventoryItemChildRequest {
  name: string;
  sku: string;
  barcode?: string;
  item_type?: string;
  current_quantity?: number;
  minimum_quantity?: number;
  description?: string;
  primary_attribute?: string;
  secondary_attribute?: string;
  notes?: string;
}

export interface InventoryItemBatchCreateRequest {
  parent: InventoryItemCreateRequest;
  children: InventoryItemChildRequest[];
}

export interface InventoryItemCreateRequest {
  name: string;
  sku: string;
  barcode?: string;
  category_id?: number;
  item_type: string;
  current_quantity: number;
  minimum_quantity: number;
  bin_id?: number;
  description?: string;
  image_url?: string;
  parent_id?: number;
}

export interface InventoryItemUpdateRequest {
  name?: string;
  category_id?: number;
  item_type?: string;
  minimum_quantity?: number;
  bin_id?: number;
  description?: string;
  image_url?: string;
  parent_id?: number;
  current_quantity?: number;
  barcode?: string;
}

export interface InventoryTransactionResponse {
  id: number;
  transaction_type: string;
  previous_quantity: number;
  change_quantity: number;
  new_quantity: number;
  reference_type?: string;
  reference_id?: number;
  reason?: string;
  created_by?: number;
  created_at: string;
}

export interface InventoryItemDetailResponse extends InventoryItemResponse {
  transactions: InventoryTransactionResponse[];
  serial_numbers?: SerialNumberResponse[];
  parent?: InventoryItemResponse;
}

export interface SerialNumberResponse {
  id: number;
  item_id: number;
  serial_number: string;
  batch_id?: string;
  unit_condition: string;
  location_bin_id?: number;
  assigned_to_order_id?: number;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface RestockRequest {
  item_id: number;
  quantity: number;
  reason: string;
}

export interface AdjustmentRequest {
  item_id: number;
  new_quantity: number;
  reason: string;
}

export const inventoryApi = {
  list: async (
    page: number = 1,
    size: number = 20,
    search?: string,
    category_id?: number,
    item_type?: string,
    low_stock: boolean = false
  ): Promise<PaginatedResponse<InventoryItemResponse>> => {
    const params = new URLSearchParams();
    params.append('page', page.toString());
    params.append('size', size.toString());
    if (search) {
      params.append('search', search);
    }
    if (category_id) {
      params.append('category_id', category_id.toString());
    }
    if (item_type) {
      params.append('item_type', item_type);
    }
    if (low_stock) {
      params.append('low_stock', 'true');
    }
    const response = await apiClient.get<PaginatedResponse<InventoryItemResponse>>(
      `/inventory/items?${params.toString()}`
    );
    return response.data;
  },

  get: async (itemId: number): Promise<InventoryItemDetailResponse> => {
    const response = await apiClient.get<InventoryItemDetailResponse>(`/inventory/items/${itemId}`);
    return response.data;
  },

  create: async (
    data: InventoryItemCreateRequest
  ): Promise<InventoryItemResponse> => {
    const response = await apiClient.post<InventoryItemResponse>('/inventory/items', data);
    return response.data;
  },

  createBatch: async (
    data: InventoryItemBatchCreateRequest
  ): Promise<InventoryItemResponse> => {
    const response = await apiClient.post<InventoryItemResponse>('/inventory/items/batch', data);
    return response.data;
  },

  update: async (
    itemId: number,
    data: InventoryItemUpdateRequest
  ): Promise<InventoryItemResponse> => {
    const response = await apiClient.patch<InventoryItemResponse>(
      `/inventory/items/${itemId}`,
      data
    );
    return response.data;
  },

  delete: async (itemId: number): Promise<void> => {
    await apiClient.delete(`/inventory/items/${itemId}`);
  },

  getByBarcode: async (barcode: string): Promise<InventoryItemResponse> => {
    const response = await apiClient.get<InventoryItemResponse>(
      `/inventory/items/barcode/${barcode}`
    );
    return response.data;
  },

  getTransactions: async (itemId: number): Promise<InventoryTransactionResponse[]> => {
    const response = await apiClient.get<InventoryTransactionResponse[]>(
      `/inventory/items/${itemId}/transactions`
    );
    return response.data;
  },

  restock: async (data: RestockRequest): Promise<InventoryTransactionResponse> => {
    const response = await apiClient.post<InventoryTransactionResponse>(
      '/inventory/restock',
      data
    );
    return response.data;
  },

  adjust: async (data: AdjustmentRequest): Promise<InventoryTransactionResponse> => {
    const response = await apiClient.post<InventoryTransactionResponse>(
      '/inventory/adjust',
      data
    );
    return response.data;
  },

  getSerials: async (itemId: number): Promise<SerialNumberResponse[]> => {
    const response = await apiClient.get<SerialNumberResponse[]>(`/inventory/${itemId}/serials`);
    return response.data;
  },

  createSingleSerials: async (itemId: number, payload: { count: number; base_serial?: string; batch_id?: string; condition?: string }): Promise<SerialNumberResponse[]> => {
    const response = await apiClient.post<SerialNumberResponse[]>(`/inventory/${itemId}/serials/single`, payload);
    return response.data;
  },

  createRangeSerials: async (itemId: number, payload: { start_serial: string; end_serial: string; batch_id?: string; condition?: string }): Promise<SerialNumberResponse[]> => {
    const response = await apiClient.post<SerialNumberResponse[]>(`/inventory/${itemId}/serials/range`, payload);
    return response.data;
  },

  importSerials: async (itemId: number, payload: { serials: string[]; batch_id?: string; condition?: string }): Promise<SerialNumberResponse[]> => {
    const response = await apiClient.post<SerialNumberResponse[]>(`/inventory/${itemId}/serials/import`, payload);
    return response.data;
  },

  deleteSerial: async (itemId: number, serialId: number): Promise<void> => {
    await apiClient.delete(`/inventory/${itemId}/serials/${serialId}`);
  },

  updateSerial: async (itemId: number, serialId: number, data: { unit_condition?: string; notes?: string }): Promise<SerialNumberResponse> => {
    const response = await apiClient.patch<SerialNumberResponse>(`/inventory/${itemId}/serials/${serialId}`, data);
    return response.data;
  },
};
