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
  created_at: string;
  updated_at: string;
  deleted_at?: string;
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
}

export interface InventoryItemUpdateRequest {
  name?: string;
  description?: string;
  minimum_quantity?: number;
  image_url?: string;
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
};
