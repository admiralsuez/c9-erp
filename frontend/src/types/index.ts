// Auth Types
export interface User {
  id: number;
  full_name: string;
  email: string;
  role_id: number;
  role?: Role & { permissions?: Permission[] };
  department?: string;
  is_active: boolean;
  created_at: string;
}

export interface Role {
  id: number;
  name: string;
  description?: string;
}

export interface Permission {
  id: number;
  code: string;
  description?: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  user: User;
}

// Inventory Types
export interface InventoryItem {
  id: number;
  name: string;
  sku: string;
  barcode?: string;
  qr_code_data?: string;
  category_id?: number;
  item_type: 'consumable' | 'returnable';
  current_quantity: number;
  reserved_quantity: number;
  minimum_quantity: number;
  bin_id?: number;
  description?: string;
  image_url?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface InventoryCategory {
  id: number;
  name: string;
  parent_id?: number;
}

export interface InventoryTransaction {
  id: number;
  item_id: number;
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

// Vendor Types
export interface Vendor {
  id: number;
  name: string;
  vendor_type?: string;
  contact_person?: string;
  phone?: string;
  email?: string;
  address?: string;
  city?: string;
  state?: string;
  gst?: string;
  notes?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface VendorSummary extends Vendor {
  total_orders?: number;
  total_quantity_received?: number;
  fulfillment_rate?: number;
}

// Order Types
export interface OrderItem {
  id: number;
  order_id: number;
  item_id: number;
  quantity_ordered: number;
  quantity_reserved: number;
  quantity_dispatched: number;
  item?: InventoryItem;
}

export interface Order {
  id: number;
  order_number: string;
  vendor_id: number;
  status: OrderStatus;
  remarks?: string;
  delivery_address?: string;
  created_by?: number;
  created_at: string;
  updated_at: string;
  vendor?: Vendor;
  items?: OrderItem[];
}

export type OrderStatus =
  | 'draft'
  | 'pending_requisition'
  | 'signed_requisition_uploaded'
  | 'approved'
  | 'dispatched'
  | 'delivered'
  | 'closed'
  | 'cancelled';

export interface OrderTimeline {
  id: number;
  order_id: number;
  action: string;
  comments?: string;
  user_id?: number;
  created_at: string;
}

// Warehouse Types
export interface Warehouse {
  id: number;
  name: string;
  address?: string;
  is_active: boolean;
}

export interface WarehouseZone {
  id: number;
  warehouse_id: number;
  name: string;
}

export interface WarehouseRack {
  id: number;
  zone_id: number;
  name: string;
}

export interface WarehouseShelf {
  id: number;
  rack_id: number;
  name: string;
}

export interface WarehouseBin {
  id: number;
  shelf_id: number;
  name: string;
}

// Dashboard Types
export interface DashboardSummary {
  total_items: number;
  low_stock_count: number;
  pending_approvals: number;
  orders_awaiting_dispatch: number;
  total_stock_value?: number;
}

export interface ActivityFeedItem {
  id: string;
  type: 'order' | 'inventory' | 'vendor' | 'notification';
  title: string;
  description?: string;
  timestamp: string;
  entity_id?: number;
  icon?: string;
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// Form Types
export interface LoginFormData {
  email: string;
  password: string;
}

export interface CreateItemFormData {
  name: string;
  sku: string;
  barcode?: string;
  category_id?: number;
  item_type: 'consumable' | 'returnable';
  minimum_quantity: number;
  opening_quantity?: number;
  bin_id?: number;
  description?: string;
  image_url?: string;
}

export interface CreateOrderFormData {
  vendor_id: number;
  items: Array<{
    item_id: number;
    quantity_ordered: number;
  }>;
  remarks?: string;
  delivery_address?: string;
}
