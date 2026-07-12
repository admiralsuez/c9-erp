import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { vendorApi } from '../api/vendors';

export const useVendors = (page: number = 1, size: number = 20, search?: string) => {
  return useQuery({
    queryKey: ['vendors', page, size, search],
    queryFn: () => vendorApi.list(page, size, search),
  });
};

export const useVendor = (vendorId: number | null) => {
  return useQuery({
    queryKey: ['vendor', vendorId],
    queryFn: () => vendorApi.get(vendorId!),
    enabled: !!vendorId,
  });
};

export const useCreateVendor = (onSuccess?: (vendor: any) => void) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: any) => vendorApi.create(data),
    onSuccess: (vendor) => {
      queryClient.invalidateQueries({ queryKey: ['vendors'] });
      toast.success('Vendor created successfully');
      onSuccess?.(vendor);
    },
    onError: (err: Error) => toast.error(err.message || 'Failed to create vendor'),
  });
};

export const useUpdateVendor = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ vendorId, data }: { vendorId: number; data: any }) =>
      vendorApi.update(vendorId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendors'] });
      toast.success('Vendor updated successfully');
    },
    onError: (err: Error) => toast.error(err.message || 'Failed to update vendor'),
  });
};

export const useDeleteVendor = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (vendorId: number) => vendorApi.delete(vendorId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendors'] });
      toast.success('Vendor deleted successfully');
    },
    onError: (err: Error) => toast.error(err.message || 'Failed to delete vendor'),
  });
};
