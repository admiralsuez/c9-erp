import { apiClient } from './client';

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// ============ SETTINGS / COMPANY PROFILE ============
export interface SettingsResponse {
  id: number;
  company_name: string;
  company_logo_url?: string;
  company_gst?: string;
  company_address?: string;
  company_contact?: string;
  order_number_format: string;
  requisition_number_format: string;
  pdf_header_text?: string;
  pdf_footer_text?: string;
  default_low_stock_threshold: number;
  ho_prefix: string;
  llf_prefix: string;
  updated_at: string;
}

export interface SettingsUpdateRequest {
  company_name?: string;
  company_logo_url?: string;
  company_gst?: string;
  company_address?: string;
  company_contact?: string;
  order_number_format?: string;
  requisition_number_format?: string;
  pdf_header_text?: string;
  pdf_footer_text?: string;
  default_low_stock_threshold?: number;
  ho_prefix?: string;
  llf_prefix?: string;
}

// ============ USERS ============
export interface RoleResponse {
  id: number;
  name: string;
  description?: string;
}

export interface UserResponse {
  id: number;
  full_name: string;
  email: string;
  department?: string;
  location?: string;
  role: RoleResponse;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ApproverResponse {
  id: number;
  full_name: string;
  email: string;
  department?: string;
  role_id: number;
  role_name?: string;
}

export interface UserCreateRequest {
  full_name: string;
  email: string;
  password: string;
  role_id: number;
  department?: string;
  location?: string;
}

export interface UserUpdateRequest {
  full_name?: string;
  email?: string;
  department?: string;
  role_id?: number;
  location?: string;
}

// ============ WAREHOUSE ============
export interface WarehouseBinResponse {
  id: number;
  name: string;
}

export interface WarehouseShelfResponse {
  id: number;
  name: string;
  bins: WarehouseBinResponse[];
}

export interface WarehouseRackResponse {
  id: number;
  name: string;
  shelves: WarehouseShelfResponse[];
}

export interface WarehouseZoneResponse {
  id: number;
  name: string;
  racks: WarehouseRackResponse[];
}

export interface WarehouseResponse {
  id: number;
  name: string;
  address?: string;
  is_active: boolean;
  zones: WarehouseZoneResponse[];
}

export interface WarehouseCreateRequest {
  name: string;
  address?: string;
}

export interface WarehouseZoneCreateRequest {
  name: string;
}

export interface WarehouseRackCreateRequest {
  name: string;
}

export interface WarehouseShelfCreateRequest {
  name: string;
}

export interface WarehouseBinCreateRequest {
  name: string;
}

// ============ PERMISSIONS ============
export interface PermissionResponse {
  id: number;
  code: string;
  description?: string;
}

// ============ APPROVAL RULES ============
export interface ApprovalRuleResponse {
  id: number;
  name: string;
  rule_type: string;
  condition_json: Record<string, any>;
  approver_role_id?: number;
  approver_user_id?: number;
  priority: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ApprovalRuleCreateRequest {
  name: string;
  rule_type: string;
  condition_json: Record<string, any>;
  approver_role_id?: number;
  approver_user_id?: number;
  priority?: number;
}

// ============ ROLES ============
export interface RoleResponse {
  id: number;
  name: string;
  description?: string;
  permissions: PermissionResponse[];
}

export interface RoleCreateRequest {
  name: string;
  description?: string;
  permission_ids: number[];
}

export interface RoleUpdateRequest {
  name?: string;
  description?: string;
  permission_ids?: number[];
}

// ============ INVENTORY CATEGORIES ============
export interface InventoryCategoryResponse {
  id: number;
  name: string;
  parent_id?: number;
}

export interface InventoryCategoryCreateRequest {
  name: string;
  parent_id?: number;
}

// ============ AUDIT LOGS ============
export interface AuditLogResponse {
  id: number;
  user_id: number;
  action: string;
  entity_type: string;
  entity_id: number;
  old_value?: string;
  new_value?: string;
  created_at: string;
}

// ============ USER SIGNATURE ============
export interface SignatureResponse {
  id: number;
  user_id: number;
  signature_data: string;
  uploaded_at: string;
  updated_at: string;
}

export interface SignatureUpdateRequest {
  signature_data: string;
}

// ============ SYSTEM INFO ============
export interface SystemInfoResponse {
  system_version: string;
  last_updated: string | null;
  database_size_mb: number;
  total_users: number;
  total_items: number;
  total_orders: number;
  active_users_30d: number;
}

// ============ API FUNCTIONS ============
export const settingsApi = {
  // Settings / Company Profile
  getSettings: async (): Promise<SettingsResponse> => {
    const response = await apiClient.get<SettingsResponse>('/settings');
    return response.data;
  },

  updateSettings: async (data: SettingsUpdateRequest): Promise<SettingsResponse> => {
    const response = await apiClient.patch<SettingsResponse>('/settings', data);
    return response.data;
  },

  uploadLogo: async (file: File): Promise<SettingsResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post<SettingsResponse>('/settings/logo', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Users
  listUsers: async (
    page: number = 1,
    size: number = 20
  ): Promise<PaginatedResponse<UserResponse>> => {
    const params = new URLSearchParams();
    params.append('page', page.toString());
    params.append('size', size.toString());
    const response = await apiClient.get<PaginatedResponse<UserResponse>>(
      `/users?${params.toString()}`
    );
    return response.data;
  },

  getUser: async (userId: number): Promise<UserResponse> => {
    const response = await apiClient.get<UserResponse>(`/users/${userId}`);
    return response.data;
  },

  createUser: async (data: UserCreateRequest): Promise<UserResponse> => {
    const response = await apiClient.post<UserResponse>('/users', data);
    return response.data;
  },

  updateUser: async (userId: number, data: UserUpdateRequest): Promise<UserResponse> => {
    const response = await apiClient.patch<UserResponse>(`/users/${userId}`, data);
    return response.data;
  },

  deleteUser: async (userId: number): Promise<void> => {
    await apiClient.delete(`/users/${userId}`);
  },

  restoreUser: async (userId: number): Promise<UserResponse> => {
    const response = await apiClient.post<UserResponse>(`/users/${userId}/restore`, {});
    return response.data;
  },

  // Approval Rules
  listApprovalRules: async (page: number = 1, size: number = 100): Promise<ApprovalRuleResponse[]> => {
    const params = new URLSearchParams();
    params.append('page', page.toString());
    params.append('size', size.toString());
    const response = await apiClient.get<ApprovalRuleResponse[]>(`/approval-rules?${params.toString()}`);
    return response.data;
  },

  createApprovalRule: async (data: ApprovalRuleCreateRequest): Promise<ApprovalRuleResponse> => {
    const response = await apiClient.post<ApprovalRuleResponse>('/approval-rules', data);
    return response.data;
  },

  updateApprovalRule: async (ruleId: number, data: ApprovalRuleCreateRequest): Promise<ApprovalRuleResponse> => {
    const response = await apiClient.patch<ApprovalRuleResponse>(`/approval-rules/${ruleId}`, data);
    return response.data;
  },

  deleteApprovalRule: async (ruleId: number): Promise<void> => {
    await apiClient.delete(`/approval-rules/${ruleId}`);
  },

  // Approvers (for order approval selection)
  listApprovers: async (
    page: number = 1,
    size: number = 100
  ): Promise<PaginatedResponse<ApproverResponse>> => {
    const params = new URLSearchParams();
    params.append('page', page.toString());
    params.append('size', size.toString());
    const response = await apiClient.get<PaginatedResponse<ApproverResponse>>(
      `/users/approvers?${params.toString()}`
    );
    return response.data;
  },

  // Roles
  listRoles: async (): Promise<RoleResponse[]> => {
    const response = await apiClient.get<RoleResponse[]>('/users/roles/list');
    return response.data;
  },

  createRole: async (data: RoleCreateRequest): Promise<RoleResponse> => {
    const response = await apiClient.post<RoleResponse>('/users/roles', data);
    return response.data;
  },

  updateRole: async (roleId: number, data: RoleUpdateRequest): Promise<RoleResponse> => {
    const response = await apiClient.patch<RoleResponse>(`/users/roles/${roleId}`, data);
    return response.data;
  },

  deleteRole: async (roleId: number): Promise<void> => {
    await apiClient.delete(`/users/roles/${roleId}`);
  },

  listPermissions: async (): Promise<PermissionResponse[]> => {
    const response = await apiClient.get<PermissionResponse[]>('/users/permissions/list');
    return response.data;
  },

  // Warehouses
  listWarehouses: async (
    page: number = 1,
    size: number = 20
  ): Promise<PaginatedResponse<WarehouseResponse>> => {
    const params = new URLSearchParams();
    params.append('page', page.toString());
    params.append('size', size.toString());
    const response = await apiClient.get<PaginatedResponse<WarehouseResponse>>(
      `/warehouses?${params.toString()}`
    );
    return response.data;
  },

  getWarehouse: async (warehouseId: number): Promise<WarehouseResponse> => {
    const response = await apiClient.get<WarehouseResponse>(`/warehouses/${warehouseId}`);
    return response.data;
  },

  createWarehouse: async (data: WarehouseCreateRequest): Promise<WarehouseResponse> => {
    const response = await apiClient.post<WarehouseResponse>('/warehouses', data);
    return response.data;
  },

  // Warehouse Zones
  createZone: async (
    warehouseId: number,
    data: WarehouseZoneCreateRequest
  ): Promise<WarehouseZoneResponse> => {
    const response = await apiClient.post<WarehouseZoneResponse>(
      `/warehouses/${warehouseId}/zones`,
      data
    );
    return response.data;
  },

  // Warehouse Racks
  createRack: async (
    warehouseId: number,
    zoneId: number,
    data: WarehouseRackCreateRequest
  ): Promise<WarehouseRackResponse> => {
    const response = await apiClient.post<WarehouseRackResponse>(
      `/warehouses/${warehouseId}/zones/${zoneId}/racks`,
      data
    );
    return response.data;
  },

  // Warehouse Shelves
  createShelf: async (
    warehouseId: number,
    zoneId: number,
    rackId: number,
    data: WarehouseShelfCreateRequest
  ): Promise<WarehouseShelfResponse> => {
    const response = await apiClient.post<WarehouseShelfResponse>(
      `/warehouses/${warehouseId}/zones/${zoneId}/racks/${rackId}/shelves`,
      data
    );
    return response.data;
  },

  // Warehouse Bins
  createBin: async (
    warehouseId: number,
    zoneId: number,
    rackId: number,
    shelfId: number,
    data: WarehouseBinCreateRequest
  ): Promise<WarehouseBinResponse> => {
    const response = await apiClient.post<WarehouseBinResponse>(
      `/warehouses/${warehouseId}/zones/${zoneId}/racks/${rackId}/shelves/${shelfId}/bins`,
      data
    );
    return response.data;
  },

  // Categories
  listCategories: async (): Promise<InventoryCategoryResponse[]> => {
    const response = await apiClient.get<InventoryCategoryResponse[]>('/inventory/categories');
    return response.data;
  },

  createCategory: async (data: InventoryCategoryCreateRequest): Promise<InventoryCategoryResponse> => {
    const response = await apiClient.post<InventoryCategoryResponse>(
      '/inventory/categories',
      data
    );
    return response.data;
  },

  updateCategory: async (categoryId: number, data: InventoryCategoryCreateRequest): Promise<InventoryCategoryResponse> => {
    const response = await apiClient.put<InventoryCategoryResponse>(
      `/inventory/categories/${categoryId}`,
      data
    );
    return response.data;
  },

  deleteCategory: async (categoryId: number): Promise<void> => {
    await apiClient.delete(`/inventory/categories/${categoryId}`);
  },

  // User Signature
  getSignature: async (userId: number): Promise<SignatureResponse> => {
    const response = await apiClient.get<SignatureResponse>(`/users/${userId}/signature`);
    return response.data;
  },

  upsertSignature: async (userId: number, data: SignatureUpdateRequest): Promise<SignatureResponse> => {
    const response = await apiClient.put<SignatureResponse>(`/users/${userId}/signature`, data);
    return response.data;
  },

  deleteSignature: async (userId: number): Promise<void> => {
    await apiClient.delete(`/users/${userId}/signature`);
  },

  // Document upload (for challan uploads)
  uploadDocument: async (orderId: number, docCategory: string, file: File, notes?: string): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);
    const params = new URLSearchParams();
    params.append('doc_category', docCategory);
    if (notes) params.append('notes', notes);
    const response = await apiClient.post(
      `/documents/upload/${orderId}?${params.toString()}`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return response.data;
  },

  // List documents for an order
  listOrderDocuments: async (orderId: number): Promise<any[]> => {
    const response = await apiClient.get(`/documents/orders/${orderId}/documents`);
    // Backend returns paginated response, extract items
    return response.data.items || response.data || [];
  },

  // Download document (returns blob)
  downloadDocument: async (documentId: number): Promise<Blob> => {
    const response = await apiClient.get(`/documents/${documentId}/download`, {
      responseType: 'blob',
    });
    return response.data;
  },

  // System Info
  getSystemInfo: async (): Promise<SystemInfoResponse> => {
    const response = await apiClient.get<SystemInfoResponse>('/settings/system-info');
    return response.data;
  },

  // Audit Logs
  listAuditLogs: async (
    page: number = 1,
    size: number = 50,
    filters?: {
      user_id?: number;
      action?: string;
      entity_type?: string;
    }
  ): Promise<PaginatedResponse<AuditLogResponse>> => {
    const params = new URLSearchParams();
    params.append('page', page.toString());
    params.append('size', size.toString());
    if (filters?.user_id) params.append('user_id', filters.user_id.toString());
    if (filters?.action) params.append('action', filters.action);
    if (filters?.entity_type) params.append('entity_type', filters.entity_type);
    const response = await apiClient.get<PaginatedResponse<AuditLogResponse>>(
      `/audit-logs?${params.toString()}`
    );
    return response.data;
  },

  // Backup & Restore
  downloadBackup: async (): Promise<Blob> => {
    const response = await apiClient.get('/backup/download', {
      responseType: 'blob',
    });
    return response.data;
  },

  uploadBackup: async (file: File): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post('/backup/restore', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  listBackups: async (): Promise<any> => {
    const response = await apiClient.get('/backup/list');
    return response.data;
  },
};
