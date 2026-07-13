import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { ordersApi } from '../api/orders';
import type { DispatchRequestBody, OrderResponse } from '../api/orders';

export const useOrders = (page: number = 1, size: number = 20, status?: string, search?: string, date_from?: string, date_to?: string, sort_by?: string, status_not?: string) => {
  return useQuery({
    queryKey: ['orders', page, size, status, search, date_from, date_to, sort_by, status_not],
    queryFn: () => ordersApi.list(page, size, status, search, date_from, date_to, sort_by, status_not),
  });
};

export const useOrder = (orderId: number | null) => {
  return useQuery({
    queryKey: ['order', orderId],
    queryFn: () => ordersApi.get(orderId!),
    enabled: !!orderId,
  });
};

export const useCreateOrder = (onSuccess?: (order: any) => void) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: any) => ordersApi.create(data),
    onSuccess: (order) => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      toast.success('Order created successfully');
      onSuccess?.(order);
    },
    onError: (err: Error) => {
      toast.error(err.message || 'Failed to create order');
    },
  });
};

export const useUpdateOrder = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ orderId, data }: { orderId: number; data: any }) =>
      ordersApi.update(orderId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      toast.success('Order updated successfully');
    },
    onError: (err: Error) => {
      toast.error(err.message || 'Failed to update order');
    },
  });
};

const useOrderLifecycleMutation = <TVars,>(
  mutationFn: (vars: TVars) => Promise<OrderResponse>
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.setQueryData(['order', data.id], data);
      queryClient.invalidateQueries({ queryKey: ['inventory'], exact: false });
      queryClient.invalidateQueries({ queryKey: ['inventory-item'], exact: false });
    },
    onError: (err: Error) => {
      toast.error(err.message || 'Operation failed');
    },
  });
};

export const useSubmitRequisition = () =>
  useOrderLifecycleMutation(
    ({ orderId, approverId }: { orderId: number; approverId?: number }) =>
      ordersApi.submitRequisition(orderId, approverId)
  );

export const useApproveWithSignature = () =>
  useOrderLifecycleMutation(
    ({ orderId, signatureData }: { orderId: number; signatureData: string }) =>
      ordersApi.approveWithSignature(orderId, signatureData)
  );

export const useUploadSignedRequisition = () =>
  useOrderLifecycleMutation(({ orderId, file }: { orderId: number; file: File }) =>
    ordersApi.uploadSigned(orderId, file)
  );

export const useApproveOrder = () =>
  useOrderLifecycleMutation((orderId: number) => ordersApi.approve(orderId));

export const useDispatchOrder = () =>
  useOrderLifecycleMutation(({ orderId, data }: { orderId: number; data: DispatchRequestBody }) =>
    ordersApi.dispatch(orderId, data)
  );

export const useDeliverOrder = () =>
  useOrderLifecycleMutation((orderId: number) => ordersApi.deliver(orderId));

export const useCloseOrder = () =>
  useOrderLifecycleMutation((orderId: number) => ordersApi.close(orderId));

export const useCancelOrder = () =>
  useOrderLifecycleMutation((orderId: number) => ordersApi.cancel(orderId));
