import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { settingsApi } from '../api/settings';
import type {
  SettingsUpdateRequest,
  UserCreateRequest,
  UserUpdateRequest,
  WarehouseCreateRequest,
  WarehouseZoneCreateRequest,
  WarehouseRackCreateRequest,
  WarehouseShelfCreateRequest,
  WarehouseBinCreateRequest,
  InventoryCategoryCreateRequest,
  RoleCreateRequest,
  RoleUpdateRequest,
  SignatureUpdateRequest,
  ApprovalRuleCreateRequest,
} from '../api/settings';

// ============ SETTINGS ============
export const useSettings = () => {
  return useQuery({
    queryKey: ['settings'],
    queryFn: () => settingsApi.getSettings(),
    retry: 1,
  });
};

export const useUpdateSettings = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: SettingsUpdateRequest) => settingsApi.updateSettings(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] });
    },
  });
};

export const useUploadLogo = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => settingsApi.uploadLogo(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] });
      toast.success('Logo uploaded successfully');
    },
    onError: (err: Error) => {
      toast.error(err.message || 'Failed to upload logo');
    },
  });
};

// ============ USERS ============
export const useUsers = (page: number = 1, size: number = 20) => {
  return useQuery({
    queryKey: ['users', page, size],
    queryFn: () => settingsApi.listUsers(page, size),
    retry: 1,
  });
};

export const useApprovers = (page: number = 1, size: number = 100) => {
  return useQuery({
    queryKey: ['approvers', page, size],
    queryFn: () => settingsApi.listApprovers(page, size),
    retry: 1,
  });
};

export const useCreateUser = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: UserCreateRequest) => settingsApi.createUser(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });
};

export const useUpdateUser = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ userId, data }: { userId: number; data: UserUpdateRequest }) =>
      settingsApi.updateUser(userId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });
};

export const useDeleteUser = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (userId: number) => settingsApi.deleteUser(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });
};

export const useRestoreUser = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (userId: number) => settingsApi.restoreUser(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });
};

// ============ APPROVAL RULES ============
export const useApprovalRules = () => {
  return useQuery({
    queryKey: ['approval-rules'],
    queryFn: () => settingsApi.listApprovalRules(),
    retry: 1,
  });
};

export const useCreateApprovalRule = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ApprovalRuleCreateRequest) => settingsApi.createApprovalRule(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approval-rules'] });
    },
  });
};

export const useUpdateApprovalRule = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ ruleId, data }: { ruleId: number; data: ApprovalRuleCreateRequest }) =>
      settingsApi.updateApprovalRule(ruleId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approval-rules'] });
    },
  });
};

export const useDeleteApprovalRule = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (ruleId: number) => settingsApi.deleteApprovalRule(ruleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approval-rules'] });
    },
  });
};

// ============ ROLES ============
export const useRoles = () => {
  return useQuery({
    queryKey: ['roles'],
    queryFn: () => settingsApi.listRoles(),
    retry: 1,
  });
};

// ============ WAREHOUSES ============
export const useWarehouses = (page: number = 1, size: number = 20) => {
  return useQuery({
    queryKey: ['warehouses', page, size],
    queryFn: () => settingsApi.listWarehouses(page, size),
    retry: 1,
  });
};

export const useWarehouse = (warehouseId: number) => {
  return useQuery({
    queryKey: ['warehouse', warehouseId],
    queryFn: () => settingsApi.getWarehouse(warehouseId),
    retry: 1,
  });
};

export const useCreateWarehouse = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: WarehouseCreateRequest) => settingsApi.createWarehouse(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['warehouses'] });
    },
  });
};

// ============ WAREHOUSE ZONES ============
export const useCreateZone = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ warehouseId, data }: { warehouseId: number; data: WarehouseZoneCreateRequest }) =>
      settingsApi.createZone(warehouseId, data),
    onSuccess: (_, { warehouseId }) => {
      queryClient.invalidateQueries({ queryKey: ['warehouse', warehouseId] });
      queryClient.invalidateQueries({ queryKey: ['warehouses'] });
    },
  });
};

// ============ WAREHOUSE RACKS ============
export const useCreateRack = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ warehouseId, zoneId, data }: { warehouseId: number; zoneId: number; data: WarehouseRackCreateRequest }) =>
      settingsApi.createRack(warehouseId, zoneId, data),
    onSuccess: (_, { warehouseId }) => {
      queryClient.invalidateQueries({ queryKey: ['warehouse', warehouseId] });
      queryClient.invalidateQueries({ queryKey: ['warehouses'] });
    },
  });
};

// ============ WAREHOUSE SHELVES ============
export const useCreateShelf = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ warehouseId, zoneId, rackId, data }: { warehouseId: number; zoneId: number; rackId: number; data: WarehouseShelfCreateRequest }) =>
      settingsApi.createShelf(warehouseId, zoneId, rackId, data),
    onSuccess: (_, { warehouseId }) => {
      queryClient.invalidateQueries({ queryKey: ['warehouse', warehouseId] });
      queryClient.invalidateQueries({ queryKey: ['warehouses'] });
    },
  });
};

// ============ WAREHOUSE BINS ============
export const useCreateBin = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ warehouseId, zoneId, rackId, shelfId, data }: { warehouseId: number; zoneId: number; rackId: number; shelfId: number; data: WarehouseBinCreateRequest }) =>
      settingsApi.createBin(warehouseId, zoneId, rackId, shelfId, data),
    onSuccess: (_, { warehouseId }) => {
      queryClient.invalidateQueries({ queryKey: ['warehouse', warehouseId] });
      queryClient.invalidateQueries({ queryKey: ['warehouses'] });
    },
  });
};

// ============ PERMISSIONS ============
export const usePermissions = () => {
  return useQuery({
    queryKey: ['permissions'],
    queryFn: () => settingsApi.listPermissions(),
    retry: 1,
  });
};

// ============ ROLE CRUD ============
export const useCreateRole = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: RoleCreateRequest) => settingsApi.createRole(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roles'] });
    },
  });
};

export const useUpdateRole = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ roleId, data }: { roleId: number; data: RoleUpdateRequest }) =>
      settingsApi.updateRole(roleId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roles'] });
    },
  });
};

export const useDeleteRole = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (roleId: number) => settingsApi.deleteRole(roleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roles'] });
    },
  });
};

// ============ CATEGORIES ============
export const useCategories = () => {
  return useQuery({
    queryKey: ['categories'],
    queryFn: () => settingsApi.listCategories(),
    retry: 1,
  });
};

export const useCreateCategory = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: InventoryCategoryCreateRequest) => settingsApi.createCategory(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] });
    },
  });
};

export const useUpdateCategory = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ categoryId, data }: { categoryId: number; data: InventoryCategoryCreateRequest }) =>
      settingsApi.updateCategory(categoryId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] });
    },
  });
};

export const useDeleteCategory = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (categoryId: number) => settingsApi.deleteCategory(categoryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] });
    },
  });
};

// ============ USER SIGNATURE ============
export const useSignature = (userId: number | null) => {
  return useQuery({
    queryKey: ['signature', userId],
    queryFn: () => settingsApi.getSignature(userId!),
    enabled: !!userId,
    retry: false,
  });
};

export const useUpsertSignature = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ userId, data }: { userId: number; data: SignatureUpdateRequest }) =>
      settingsApi.upsertSignature(userId, data),
    onSuccess: (_, { userId }) => {
      queryClient.invalidateQueries({ queryKey: ['signature', userId] });
    },
  });
};

export const useDeleteSignature = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (userId: number) => settingsApi.deleteSignature(userId),
    onSuccess: (_, userId) => {
      queryClient.invalidateQueries({ queryKey: ['signature', userId] });
    },
  });
};

// ============ DOCUMENTS ============
export const useUploadDocument = () => {
  return useMutation({
    mutationFn: ({ orderId, docCategory, file, notes }: { orderId: number; docCategory: string; file: File; notes?: string }) =>
      settingsApi.uploadDocument(orderId, docCategory, file, notes),
  });
};

export const useOrderDocuments = (orderId: number | null) => {
  return useQuery({
    queryKey: ['order-documents', orderId],
    queryFn: () => settingsApi.listOrderDocuments(orderId!),
    enabled: !!orderId,
    retry: 1,
  });
};

export const useDownloadDocument = () => {
  return useMutation({
    mutationFn: (documentId: number) => settingsApi.downloadDocument(documentId),
  });
};

// ============ SYSTEM INFO ============
export const useSystemInfo = () => {
  return useQuery({
    queryKey: ['system-info'],
    queryFn: () => settingsApi.getSystemInfo(),
    retry: 1,
  });
};

// ============ AUDIT LOGS ============
export const useAuditLogs = (
  page: number = 1,
  size: number = 50,
  filters?: {
    user_id?: number;
    action?: string;
    entity_type?: string;
  }
) => {
  return useQuery({
    queryKey: ['audit-logs', page, size, filters],
    queryFn: () => settingsApi.listAuditLogs(page, size, filters),
    retry: 1,
  });
};

// ============ BACKUP & RESTORE ============
export const useDownloadBackup = () => {
  return useMutation({
    mutationFn: () => settingsApi.downloadBackup(),
    onSuccess: (blob) => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `erp_backup_${new Date().getTime()}.db`;
      document.body.appendChild(a);
      a.click();
      URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success('Backup downloaded successfully');
    },
    onError: (err: Error) => {
      toast.error(err.message || 'Failed to download backup');
    },
  });
};

export const useUploadBackup = () => {
  return useMutation({
    mutationFn: (file: File) => settingsApi.uploadBackup(file),
    onSuccess: (data) => {
      toast.success(`Database restored successfully. Safety backup: ${data.safety_backup}`);
    },
    onError: (err: Error) => {
      toast.error(err.message || 'Failed to restore backup');
    },
  });
};

export const useListBackups = () => {
  return useQuery({
    queryKey: ['backups-list'],
    queryFn: () => settingsApi.listBackups(),
    retry: 1,
  });
};
