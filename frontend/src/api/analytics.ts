import { apiClient } from './client';

export interface RecentOrder {
  id: number;
  order_number: string;
  vendor_id: number;
  status: string;
  created_at: string;
  vendor?: { id: number; name: string };
  created_by_user?: { id: number; full_name: string };
}

export interface LowStockItem {
  id: number;
  sku: string;
  name: string;
  current: number;
  minimum: number;
}

export interface InventoryHealth {
  total_items: number;
  low_stock_count: number;
  low_stock_items: LowStockItem[];
  total_quantity: number;
}

export interface OrderMetrics {
  total_orders: number;
  by_status: Record<string, number>;
  pending_approvals: number;
  average_approval_time_days: number;
  average_dispatch_time_days: number;
}

export interface VendorPerformance {
  vendor_id: number;
  vendor_name: string;
  order_count: number;
}

export interface EmailStats {
  total_sent: number;
  delivered: number;
  failed: number;
  opened: number;
}

export interface UserActivity {
  period_days: number;
  active_users: number;
  total_actions: number;
  orders_created: number;
  top_actions: Record<string, number>;
}

export interface DashboardOverview {
  overview: {
    total_orders: number;
    pending_approvals: number;
    recent_orders: RecentOrder[];
  };
  order_metrics: OrderMetrics;
  inventory_health: InventoryHealth;
  vendor_performance: VendorPerformance[];
  email_stats: EmailStats;
  user_activity: UserActivity;
  calculated_at: string;
}

export const analyticsApi = {
  getDashboardOverview: async (limit?: number): Promise<DashboardOverview> => {
    const url = limit ? `/analytics/dashboard/overview?limit=${limit}` : '/analytics/dashboard/overview';
    const response = await apiClient.get<DashboardOverview>(url);
    return response.data;
  },
};
