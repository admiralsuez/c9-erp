import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, ListLoadingState, ListEmptyState } from '../../components/ui';
import { useAuth } from '../../hooks/useAuth';
import { formatDateTime } from '../../utils/format';
import { useOrders, useApproveWithSignature } from '../../hooks/useOrders';
import { useSignature } from '../../hooks/useSettings';
import { ClipboardCheck, AlertCircle, CheckCircle, Eye, PenTool } from 'lucide-react';

export const ApprovalsPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { data: pendingOrders, isLoading, error } = useOrders(1, 50, 'pending_requisition');
  const { data: mySignature } = useSignature(user?.id ?? null);
  const approveWithSignature = useApproveWithSignature();
  const [approvingId, setApprovingId] = useState<number | null>(null);
  const [actionError, setActionError] = useState('');

  const handleApprove = async (orderId: number) => {
    if (!mySignature?.signature_data) {
      setActionError('Please set up your digital signature in Settings first.');
      return;
    }
    setApprovingId(orderId);
    setActionError('');
    try {
      await approveWithSignature.mutateAsync({ orderId, signatureData: mySignature.signature_data });
    } catch (err: any) {
      setActionError(err?.response?.data?.detail || 'Failed to approve');
    } finally {
      setApprovingId(null);
    }
  };

  if (isLoading) return <ListLoadingState message="Loading approvals..." />;

  const items = pendingOrders?.items ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-neutral-900">My Approvals</h1>
        <p className="text-neutral-600 mt-1">Requisitions waiting for your approval</p>
      </div>

      {error && (
        <Card className="bg-error/10 border border-error" padding="lg">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-error" />
            <p className="text-error">Failed to load approvals</p>
          </div>
        </Card>
      )}

      {actionError && (
        <Card className="bg-error/10 border border-error" padding="lg">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-error" />
            <p className="text-error">{actionError}</p>
          </div>
        </Card>
      )}

      {!mySignature && (
        <Card className="bg-warning/10 border border-warning/30" padding="lg">
          <div className="flex items-center gap-3">
            <PenTool className="w-5 h-5 text-warning flex-shrink-0" />
            <p className="text-warning text-sm">
              You haven't set up your digital signature yet.{' '}
              <button onClick={() => navigate('/settings')} className="underline font-medium">
                Go to Settings
              </button>{' '}
              to add one before approving.
            </p>
          </div>
        </Card>
      )}

      {items.length === 0 ? (
        <ListEmptyState icon={<ClipboardCheck className="w-12 h-12 text-neutral-300 mx-auto mb-3" />} message="No pending approvals" />
      ) : (
        <div className="space-y-3">
          {items.map((order: any) => (
            <Card key={order.id} padding="lg">
              <div className="flex items-center justify-between flex-wrap gap-4">
                <div className="flex-1 min-w-0">
                  <button
                    onClick={() => navigate(`/orders/${order.id}`)}
                    className="font-semibold text-primary-600 hover:underline text-left"
                  >
                    {order.order_number}
                  </button>
                  <p className="text-sm text-neutral-500 mt-1">
                    {order.vendor?.name || `Vendor #${order.vendor_id}`} • {order.items?.length || 0} items
                  </p>
                  <p className="text-xs text-neutral-400">
                    Created {formatDateTime(order.created_at)}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button variant="secondary" size="sm" onClick={() => navigate(`/orders/${order.id}`)}>
                    <Eye className="w-4 h-4" />
                    View
                  </Button>
                  <Button
                    size="sm"
                    onClick={() => handleApprove(order.id)}
                    disabled={approvingId === order.id || !mySignature}
                    className="bg-success text-white hover:bg-success/90"
                  >
                    {approvingId === order.id ? <span className="animate-spin inline-block w-4 h-4 border-2 border-current border-t-transparent rounded-full" /> : <CheckCircle className="w-4 h-4" />}
                    {approvingId === order.id ? 'Approving...' : 'Approve & Sign'}
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default ApprovalsPage;
