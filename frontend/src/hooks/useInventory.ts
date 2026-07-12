import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { inventoryApi } from '../api/inventory';
import type { RestockRequest, AdjustmentRequest, InventoryItemCreateRequest, InventoryItemUpdateRequest, InventoryItemResponse } from '../api/inventory';

export const useInventory = (
  page: number = 1,
  size: number = 20,
  search?: string,
  category_id?: number,
  item_type?: string,
  low_stock?: boolean
) => {
  return useQuery({
    queryKey: ['inventory', page, size, search, category_id, item_type, low_stock],
    queryFn: () => inventoryApi.list(page, size, search, category_id, item_type, low_stock),
  });
};

export const useInventoryItem = (itemId: number | null) => {
  return useQuery({
    queryKey: ['inventory-item', itemId],
    queryFn: () => inventoryApi.get(itemId!),
    enabled: !!itemId,
  });
};

export const useCreateInventoryItem = (onSuccess?: (item: InventoryItemResponse) => void) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: InventoryItemCreateRequest) => inventoryApi.create(data),
    onSuccess: (item) => {
      queryClient.invalidateQueries({ queryKey: ['inventory'], exact: false });
      toast.success('Item created successfully');
      onSuccess?.(item);
    },
    onError: (err: Error) => toast.error(err.message || 'Failed to create item'),
  });
};

export const useUpdateInventoryItem = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ itemId, data }: { itemId: number; data: InventoryItemUpdateRequest }) =>
      inventoryApi.update(itemId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inventory'], exact: false });
      toast.success('Item updated successfully');
    },
    onError: (err: Error) => toast.error(err.message || 'Failed to update item'),
  });
};

export const useDeleteInventoryItem = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (itemId: number) => inventoryApi.delete(itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inventory'], exact: false });
      toast.success('Item deleted successfully');
    },
    onError: (err: Error) => toast.error(err.message || 'Failed to delete item'),
  });
};

export const useInventoryByBarcode = (barcode: string | null) => {
  return useQuery({
    queryKey: ['inventory-barcode', barcode],
    queryFn: () => inventoryApi.getByBarcode(barcode!),
    enabled: !!barcode,
  });
};

export const useRestockItem = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: RestockRequest) => inventoryApi.restock(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inventory'], exact: false });
      queryClient.invalidateQueries({ queryKey: ['inventory-item'], exact: false });
      toast.success('Item restocked');
    },
    onError: (err: Error) => toast.error(err.message || 'Failed to restock item'),
  });
};

export const useAdjustItem = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: AdjustmentRequest) => inventoryApi.adjust(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inventory'], exact: false });
      queryClient.invalidateQueries({ queryKey: ['inventory-item'], exact: false });
      toast.success('Stock adjusted');
    },
    onError: (err: Error) => toast.error(err.message || 'Failed to adjust stock'),
  });
};
