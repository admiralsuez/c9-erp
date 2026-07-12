import React from 'react';
import { Card } from '../components/ui/Card';
import { StatCard } from '../components/common/StatCard';
import { EntityListCard } from '../components/common/EntityListCard';
import { Loader, Package, AlertCircle, Clock, TrendingUp, Lock } from 'lucide-react';
import { useDashboardOverview } from '../hooks/useDashboard';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

const statusLabels: Record<string, string> = {
  draft: 'Draft',
  pending_requisition: 'Pending Requisition',
  pending_approval: 'Pending Approval',
  signed_requisition_uploaded: 'Signed Uploaded',
  approved: 'Approved',
  dispatched: 'Dispatched',
  delivered: 'Delivered',
  closed: 'Closed',
  cancelled: 'Cancelled',
};

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const { data, isLoading, error } = useDashboardOverview(10);
  const navigate = useNavigate();

  // Check if user has dashboard.view permission
  const hasDashboardPermission = user?.role?.permissions?.some(
    (perm: any) => perm.code === 'dashboard.view'
  ) ?? false;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    );
  }

  if (!hasDashboardPermission) {
    return (
      <div className="space-y-6 pb-6">
        <h1 className="text-3xl font-bold text-neutral-900">Dashboard</h1>
        <Card padding="lg" className="bg-warning/10 border border-warning/30">
          <div className="flex items-center gap-3">
            <Lock className="w-5 h-5 text-warning" />
            <div>
              <p className="font-semibold text-warning mb-1">Access Denied</p>
              <p className="text-warning/90">Your role ({user?.role?.name || 'Unknown'}) does not have permission to view the dashboard. Please contact your administrator if you believe this is incorrect.</p>
            </div>
          </div>
        </Card>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="space-y-6 pb-6">
        <h1 className="text-3xl font-bold text-neutral-900">Dashboard</h1>
        <Card padding="lg" className="bg-error/10 border border-error/30">
          <p className="text-error">Could not load dashboard data. Please try again or contact support.</p>
        </Card>
      </div>
    );
  }

  const { overview, inventory_health, order_metrics, vendor_performance, user_activity } = data;
  const recentOrders = (overview.recent_orders || []).slice(0, 10);
  const lowStockCount = inventory_health?.low_stock_count ?? 0;
  const totalItems = inventory_health?.total_items ?? 0;
  const pendingApprovals = overview.pending_approvals ?? 0;
  const totalQuantity = inventory_health?.total_quantity ?? 0;

  const statsCards = [
    {
      label: 'Total Items',
      value: totalItems.toLocaleString(),
      trend: 'neutral' as const,
      trendValue: `${lowStockCount} low stock items`,
      onClick: () => navigate('/inventory'),
    },
    {
      label: 'Low Stock',
      value: lowStockCount.toString(),
      trend: (lowStockCount > 0 ? 'down' : 'up') as 'up' | 'down',
      trendValue: lowStockCount > 0 ? 'Needs attention' : 'All stocked up',
      onClick: () => navigate('/inventory?low_stock=true'),
    },
    {
      label: 'Pending Approvals',
      value: pendingApprovals.toString(),
      trend: 'neutral' as const,
      trendValue: pendingApprovals > 0 ? 'Awaiting action' : 'All clear',
      onClick: () => navigate('/approvals'),
    },
    {
      label: 'Total Orders',
      value: order_metrics?.total_orders?.toString() ?? '0',
      trend: 'up' as const,
      trendValue: `${Object.keys(order_metrics?.by_status ?? {}).length} statuses`,
      onClick: () => navigate('/orders'),
    },
  ];

  return (
    <div className="space-y-6 pb-6">
      <div>
        <h1 className="text-3xl font-bold text-neutral-900">Dashboard</h1>
        <p className="text-neutral-600 mt-1">Welcome back! Here's your inventory overview.</p>
      </div>

      <Card padding="lg" className="bg-gradient-to-r from-primary-50 to-primary-100 border-primary-200">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="cursor-pointer hover:opacity-80 transition-opacity" onClick={() => navigate('/orders')}>
            <p className="text-sm text-primary-700 font-medium">Total Orders</p>
            <p className="text-3xl font-bold text-primary-900 mt-1">{order_metrics?.total_orders ?? 0}</p>
          </div>
          <div className="cursor-pointer hover:opacity-80 transition-opacity" onClick={() => navigate('/approvals')}>
            <p className="text-sm text-primary-700 font-medium">Pending Approvals</p>
            <p className="text-3xl font-bold text-primary-900 mt-1">{pendingApprovals}</p>
          </div>
          <div className="cursor-pointer hover:opacity-80 transition-opacity" onClick={() => navigate('/inventory')}>
            <p className="text-sm text-primary-700 font-medium">Inventory Items</p>
            <p className="text-3xl font-bold text-primary-900 mt-1">{totalItems}</p>
          </div>
          <div className="cursor-pointer hover:opacity-80 transition-opacity" onClick={() => navigate('/settings')}>
            <p className="text-sm text-primary-700 font-medium">Active Users (30d)</p>
            <p className="text-3xl font-bold text-primary-900 mt-1">{user_activity?.active_users ?? 0}</p>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statsCards.map((stat, index) => (
          <StatCard
            key={index}
            label={stat.label}
            value={stat.value}
            trend={stat.trend}
            trendValue={stat.trendValue}
            onClick={stat.onClick}
            icon={
              index === 0 ? (
                <Package className="w-8 h-8" />
              ) : index === 1 ? (
                <AlertCircle className="w-8 h-8" />
              ) : index === 2 ? (
                <Clock className="w-8 h-8" />
              ) : (
                <TrendingUp className="w-8 h-8" />
              )
            }
          />
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card padding="lg">
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-neutral-900">Recent Orders</h2>
            </div>
            <div className="space-y-2">
              {recentOrders.length === 0 && (
                <p className="text-sm text-neutral-500">No orders yet.</p>
              )}
              {recentOrders.map((order) => (
                <EntityListCard
                  key={order.id}
                  title={order.order_number || `Order #${order.id}`}
                  subtitle={order.vendor?.name || `Vendor #${order.vendor_id}`}
                  description={statusLabels[order.status] || order.status}
                  onClick={() => navigate(`/orders/${order.id}`)}
                />
              ))}
            </div>
            <button
              onClick={() => navigate('/orders')}
              className="w-full mt-4 py-2 text-primary-600 hover:text-primary-700 font-medium text-sm transition-colors"
            >
              View all orders →
            </button>
          </Card>
        </div>

        <Card padding="lg">
          <h2 className="text-lg font-semibold text-neutral-900 mb-4">Health Metrics</h2>
          <div className="space-y-4">
            <div className="cursor-pointer hover:opacity-80 transition-opacity" onClick={() => navigate('/inventory')}>
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm text-neutral-600">Total Quantity</span>
                <span className="text-sm font-semibold text-success">{totalQuantity.toLocaleString()}</span>
              </div>
              <div className="w-full bg-neutral-200 rounded-full h-2">
                <div className="bg-primary-600 h-2 rounded-full" style={{ width: '100%' }} />
              </div>
            </div>
            <div className="cursor-pointer hover:opacity-80 transition-opacity" onClick={() => navigate('/inventory?low_stock=true')}>
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm text-neutral-600">Low Stock Items</span>
                <span className={`text-sm font-semibold ${lowStockCount > 0 ? 'text-warning' : 'text-success'}`}>
                  {lowStockCount}
                </span>
              </div>
              <div className="w-full bg-neutral-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${lowStockCount > 0 ? 'bg-warning' : 'bg-success'}`}
                  style={{ width: `${Math.min(100, (lowStockCount / Math.max(totalItems, 1)) * 100)}%` }}
                />
              </div>
            </div>
            <div className="cursor-pointer hover:opacity-80 transition-opacity" onClick={() => navigate('/vendors')}>
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm text-neutral-600">Vendors</span>
                <span className="text-sm font-semibold text-info">{vendor_performance?.length ?? 0}</span>
              </div>
            </div>
            {order_metrics?.average_approval_time_days !== undefined && (
              <div>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm text-neutral-600">Avg Approval (days)</span>
                  <span className="text-sm font-semibold text-neutral-900">
                    {order_metrics.average_approval_time_days}
                  </span>
                </div>
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
};

export default DashboardPage;
