import React, { useRef, useState } from 'react';
import { ImageCropModal } from '../../components/ImageCropModal';
import { useNavigate, useParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import { Card, Button, ListLoadingState, StatusBadge } from '../../components/ui';
import { cardError, cardErrorPadded, formLabel } from '../../styles/classNames';
import {
  ArrowLeft,
  Loader,
  AlertCircle,
  Send,
  Upload,
  CheckCircle,
  Truck,
  PackageCheck,
  Archive,
  XCircle,
  Eye,
  FileDown,
} from 'lucide-react';
import {
  useOrder,
  useSubmitRequisition,
  useUploadSignedRequisition,
  useApproveOrder,
  useDispatchOrder,
  useDeliverOrder,
  useCloseOrder,
  useCancelOrder,
} from '../../hooks/useOrders';
import { useVendor } from '../../hooks/useVendors';
import { useInventory } from '../../hooks/useInventory';
import { useUserNameMap } from '../../hooks/useUsers';
import { useAuth } from '../../hooks/useAuth';
import { useSignature, useUploadDocument, useOrderDocuments, useDownloadDocument, useApprovers } from '../../hooks/useSettings';
import { formatDate, formatDateTime } from '../../utils/format';

const STATUS_FLOW = [
  'draft',
  'pending_requisition',
  'signed_requisition_uploaded',
  'approved',
  'dispatched',
  'delivered',
  'closed',
];

const formatStatus = (status: string) =>
  status
    .replace(/_/g, ' ')
    .split(' ')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');

const getApiError = (error: any, fallback: string): string => {
  const detail = error?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (detail?.message) {
    const extra = Array.isArray(detail.errors) ? ` ${detail.errors.join('; ')}` : '';
    return `${detail.message}.${extra}`;
  }
  return error?.message || fallback;
};

export const OrderDetailPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const orderId = id ? parseInt(id) : null;
  const { user: currentUser } = useAuth();

  const { data: order, isLoading, error } = useOrder(orderId);
  const { data: vendor } = useVendor(order?.vendor_id ?? null);
  const { data: inventoryData } = useInventory(1, 100);
  const userNames = useUserNameMap();

  const { data: mySignature } = useSignature(currentUser?.id ?? null);

  const submitRequisition = useSubmitRequisition();
  const uploadSigned = useUploadSignedRequisition();
  const approveOrder = useApproveOrder();
  const dispatchOrder = useDispatchOrder();
  const deliverOrder = useDeliverOrder();
  const closeOrder = useCloseOrder();
  const cancelOrder = useCancelOrder();
  const uploadDocument = useUploadDocument();
  const { data: documents } = useOrderDocuments(orderId);
  const downloadDocument = useDownloadDocument();

  const [actionError, setActionError] = useState('');
  const [cancelConfirm, setCancelConfirm] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Approver selection
  const [approverModalOpen, setApproverModalOpen] = useState(false);
  const [selectedApproverId, setSelectedApproverId] = useState<number | null>(null);
  // Use approvers endpoint for order approval selection
  const { data: approversData, isLoading: approversLoading } = useApprovers(1, 500);

  // Dispatch challan modal
  const [dispatchModalOpen, setDispatchModalOpen] = useState(false);
  const [dispatchChallanFile, setDispatchChallanFile] = useState<File | null>(null);
  const dispatchChallanRef = useRef<HTMLInputElement>(null);

  // Deliver signed challan modal
  const [deliverModalOpen, setDeliverModalOpen] = useState(false);
  const [deliverChallanFile, setDeliverChallanFile] = useState<File | null>(null);
  const [verificationChecked, setVerificationChecked] = useState(false);
  const [signaturePresent, setSignaturePresent] = useState(false);
  const [datePresent, setDatePresent] = useState(false);
  const [receiverNamePresent, setReceiverNamePresent] = useState(false);
  const deliverChallanRef = useRef<HTMLInputElement>(null);

  const isActing =
    submitRequisition.isPending ||
    uploadSigned.isPending ||
    approveOrder.isPending ||
    dispatchOrder.isPending ||
    deliverOrder.isPending ||
    closeOrder.isPending ||
    cancelOrder.isPending ||
    uploadDocument.isPending;

  const itemMap: Record<number, { name: string; sku: string }> = {};
  for (const inv of inventoryData?.items ?? []) {
    itemMap[inv.id] = { name: inv.name, sku: inv.sku };
  }

  const userLabel = (userId?: number | null) =>
    userId ? userNames[userId] || `User #${userId}` : 'Unknown';

  const runAction = (action: () => void) => {
    setActionError('');
    action();
  };

  const onError = (err: any, fallback: string) => setActionError(getApiError(err, fallback));

  const [cropFile, setCropFile] = useState<File | null>(null);

  const handleFileSelected = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !orderId) return;
    setActionError('');
    e.target.value = '';
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (ext === 'pdf') {
      uploadSigned.mutate(
        { orderId, file },
        { onError: (err: any) => onError(err, 'Failed to upload signed requisition') }
      );
    } else {
      setCropFile(file);
    }
  };

  const handleCropConfirm = (croppedFile: File) => {
    setCropFile(null);
    if (!orderId) return;
    uploadSigned.mutate(
      { orderId, file: croppedFile },
      { onError: (err: any) => onError(err, 'Failed to upload signed requisition') }
    );
  };

  // === Dispatch with challan ===
  const handleOpenDispatchModal = () => {
    setDispatchModalOpen(true);
    setDispatchChallanFile(null);
    setActionError('');
  };

  const handleDispatchWithChallan = async () => {
    if (!order || !orderId) return;
    setActionError('');

    try {
      // 1. Upload challan if provided
      if (dispatchChallanFile) {
        await uploadDocument.mutateAsync({
          orderId,
          docCategory: 'dispatch_challan',
          file: dispatchChallanFile,
          notes: `Dispatch challan for ${order.order_number}`,
        });
      }

      // 2. Dispatch the order
      await dispatchOrder.mutateAsync({
        orderId,
        data: {
          items: order.items.map((it: any) => ({
            item_id: it.item_id,
            quantity: Number(it.quantity_reserved),
          })),
        },
      });

      setDispatchModalOpen(false);
    } catch (err: any) {
      onError(err, 'Failed to dispatch order');
    }
  };

  // === Deliver with signed challan ===
  const handleOpenDeliverModal = () => {
    setDeliverModalOpen(true);
    setDeliverChallanFile(null);
    setVerificationChecked(false);
    setSignaturePresent(false);
    setDatePresent(false);
    setReceiverNamePresent(false);
    setActionError('');
  };

  const handleDeliverWithChallan = async () => {
    if (!order || !orderId) return;
    setActionError('');

    if (!verificationChecked) {
      setActionError('Please confirm that you have verified the signed challan.');
      return;
    }

    try {
      // 1. Upload signed challan
      if (deliverChallanFile) {
        await uploadDocument.mutateAsync({
          orderId,
          docCategory: 'signed_delivery_challan',
          file: deliverChallanFile,
          notes: `Signed delivery challan for ${order.order_number}`,
        });
      }

      // 2. Mark as delivered
      await deliverOrder.mutateAsync(order.id);
      setDeliverModalOpen(false);
    } catch (err: any) {
      onError(err, 'Failed to mark order delivered');
    }
  };

  if (isLoading) return <ListLoadingState message="Loading order..." />;

  if (error || !order) {
    return (
      <div className="space-y-6 pb-6">
        <button
          onClick={() => navigate('/orders')}
          className="p-2 hover:bg-neutral-100 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5 text-neutral-600" />
        </button>
        <Card className={cardErrorPadded} padding="lg">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-error flex-shrink-0" />
            <p className="text-error">
              {error instanceof Error ? error.message : 'Order not found'}
            </p>
          </div>
        </Card>
      </div>
    );
  }

  const statusIndex = STATUS_FLOW.indexOf(order.status);
  const isTerminal = order.status === 'closed' || order.status === 'cancelled';
  const timeline = [...(order.timeline_entries ?? [])].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  return (
    <div className="space-y-6 pb-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/orders')}
            className="p-2 hover:bg-neutral-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-neutral-600" />
          </button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold text-neutral-900">{order.order_number}</h1>
              <StatusBadge status={order.status}>{formatStatus(order.status)}</StatusBadge>
            </div>
            <p className="text-neutral-600 mt-1">
              Vendor: {vendor?.name || `#${order.vendor_id}`} • Created by{' '}
              {userLabel(order.created_by)} on {formatDate(order.created_at)}
            </p>
          </div>
        </div>

        {/* Lifecycle Action Buttons */}
        <div className="flex gap-2 flex-wrap">
          {order.status === 'draft' && (
            <Button
              onClick={() => setApproverModalOpen(true)}
              disabled={isActing}
              className="flex items-center gap-2 bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50"
            >
              <Send className="w-4 h-4" />
              Submit Requisition
            </Button>
          )}

          {/* Download PDF button (available for all orders) */}
          <Button
            variant="secondary"
            size="sm"
            onClick={async () => {
              try {
                const apiClient = (await import('../../api/client')).default;
                const resp = await apiClient.get(`/orders/${order.id}/download-pdf`, {
                  responseType: 'blob',
                });
                const url = URL.createObjectURL(resp.data);
                window.open(url, '_blank');
                setTimeout(() => URL.revokeObjectURL(url), 60000);
              } catch {
                toast.error('Failed to download PDF');
              }
            }}
            className="flex items-center gap-1"
          >
            <FileDown className="w-4 h-4" />
            PDF
          </Button>

          {order.status === 'pending_requisition' && (
            <>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.jpg,.jpeg,.png"
                className="hidden"
                onChange={handleFileSelected}
              />
              <Button
                onClick={() => fileInputRef.current?.click()}
                disabled={isActing}
                className="flex items-center gap-2 bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50"
              >
                {uploadSigned.isPending ? (
                  <Loader className="w-4 h-4 animate-spin" />
                ) : (
                  <Upload className="w-4 h-4" />
                )}
                Upload Signed Requisition
              </Button>
            </>
          )}

          {order.status === 'signed_requisition_uploaded' && (
            <Button
              onClick={() =>
                runAction(() =>
                  approveOrder.mutate(order.id, {
                    onError: (err: any) => onError(err, 'Failed to approve order'),
                  })
                )
              }
              disabled={isActing}
              className="flex items-center gap-2 bg-success text-white hover:bg-success/90 disabled:opacity-50"
            >
              {approveOrder.isPending ? (
                <Loader className="w-4 h-4 animate-spin" />
              ) : (
                <CheckCircle className="w-4 h-4" />
              )}
              {mySignature ? 'Approve (with Signature)' : 'Approve (Reserve Stock)'}
            </Button>
          )}

          {order.status === 'approved' && (
            <Button
              onClick={handleOpenDispatchModal}
              disabled={isActing}
              className="flex items-center gap-2 bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50"
            >
              {isActing ? (
                <Loader className="w-4 h-4 animate-spin" />
              ) : (
                <Truck className="w-4 h-4" />
              )}
              Dispatch with Challan
            </Button>
          )}

          {order.status === 'dispatched' && (
            <Button
              onClick={handleOpenDeliverModal}
              disabled={isActing}
              className="flex items-center gap-2 bg-success text-white hover:bg-success/90 disabled:opacity-50"
            >
              {isActing ? (
                <Loader className="w-4 h-4 animate-spin" />
              ) : (
                <PackageCheck className="w-4 h-4" />
              )}
              Deliver with Signed Challan
            </Button>
          )}

          {order.status === 'delivered' && (
            <Button
              onClick={() =>
                runAction(() =>
                  closeOrder.mutate(order.id, {
                    onError: (err: any) => onError(err, 'Failed to close order'),
                  })
                )
              }
              disabled={isActing}
              className="flex items-center gap-2 bg-neutral-700 text-white hover:bg-neutral-800 disabled:opacity-50"
            >
              {closeOrder.isPending ? (
                <Loader className="w-4 h-4 animate-spin" />
              ) : (
                <Archive className="w-4 h-4" />
              )}
              Close Order
            </Button>
          )}

          {!isTerminal && (
            <Button
              onClick={() => setCancelConfirm(true)}
              disabled={isActing}
              className="flex items-center gap-2 bg-error/10 text-error hover:bg-error/20 disabled:opacity-50"
            >
              <XCircle className="w-4 h-4" />
              Cancel Order
            </Button>
          )}
        </div>
      </div>

      {/* Status Progress */}
      {order.status !== 'cancelled' && (
        <Card padding="lg">
          <div className="flex items-center gap-1 overflow-x-auto">
            {STATUS_FLOW.map((step, idx) => (
              <React.Fragment key={step}>
                <div className="flex flex-col items-center min-w-20">
                  <div
                    className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold ${
                      idx < statusIndex
                        ? 'bg-success text-white'
                        : idx === statusIndex
                          ? 'bg-primary-600 text-white'
                          : 'bg-neutral-200 text-neutral-500'
                    }`}
                  >
                    {idx + 1}
                  </div>
                  <p
                    className={`text-xs mt-1 text-center ${
                      idx === statusIndex ? 'font-semibold text-neutral-900' : 'text-neutral-500'
                    }`}
                  >
                    {formatStatus(step)}
                  </p>
                </div>
                {idx < STATUS_FLOW.length - 1 && (
                  <div
                    className={`flex-1 h-0.5 min-w-4 mb-4 ${
                      idx < statusIndex ? 'bg-success' : 'bg-neutral-200'
                    }`}
                  />
                )}
              </React.Fragment>
            ))}
          </div>
        </Card>
      )}

      {/* Error Banner */}
      {actionError && (
        <Card className={cardError} padding="lg">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-error flex-shrink-0" />
            <p className="text-error">{actionError}</p>
          </div>
        </Card>
      )}

      {/* Cancel Confirmation */}
      {cancelConfirm && (
        <Card className="border border-error bg-error/5 p-6" padding="lg">
          <h3 className="text-lg font-semibold text-neutral-900 mb-2">Cancel Order?</h3>
          <p className="text-neutral-600 mb-4">
            This will cancel <strong>{order.order_number}</strong>
            {order.status === 'approved' && ' and release all reserved stock'}. This action cannot
            be undone.
          </p>
          <div className="flex gap-3 justify-end">
            <Button
              onClick={() => setCancelConfirm(false)}
              disabled={cancelOrder.isPending}
              className="px-4 py-2 border border-neutral-300 rounded-lg text-neutral-700 hover:bg-neutral-50"
            >
              Keep Order
            </Button>
            <Button
              onClick={() =>
                runAction(() =>
                  cancelOrder.mutate(order.id, {
                    onSuccess: () => setCancelConfirm(false),
                    onError: (err: any) => {
                      onError(err, 'Failed to cancel order');
                      setCancelConfirm(false);
                    },
                  })
                )
              }
              disabled={cancelOrder.isPending}
              className="px-4 py-2 bg-error text-white hover:bg-error/90 flex items-center gap-2"
            >
              {cancelOrder.isPending && <Loader className="w-4 h-4 animate-spin" />}
              {cancelOrder.isPending ? 'Cancelling...' : 'Cancel Order'}
            </Button>
          </div>
        </Card>
      )}

      {/* Approver Selection Modal */}
      {approverModalOpen && (
        <Card className="border border-primary-300 bg-primary-50/30 p-6" padding="lg">
          <h3 className="text-lg font-semibold text-neutral-900 mb-2">Select Approver</h3>
          <p className="text-neutral-600 mb-4">
            Choose who should approve this requisition for <strong>{order.order_number}</strong>.
          </p>
          <div className="space-y-3 mb-4 max-h-60 overflow-y-auto">
            {approversLoading && (
              <p className="text-sm text-neutral-500 p-3">Loading approvers...</p>
            )}
            {!approversLoading && (!approversData?.items || approversData.items.length === 0) && (
              <p className="text-sm text-neutral-500 p-3">No approvers available</p>
            )}
            {(approversData?.items ?? []).map((u: any) => (
              <label
                key={u.id}
                className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                  selectedApproverId === u.id
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-neutral-200 hover:bg-neutral-50'
                }`}
              >
                <input
                  type="radio"
                  name="approver"
                  checked={selectedApproverId === u.id}
                  onChange={() => setSelectedApproverId(u.id)}
                  className="w-4 h-4 text-primary-600"
                />
                <div>
                  <p className="text-sm font-medium text-neutral-900">{u.full_name}</p>
                  <p className="text-xs text-neutral-500">{u.email} • {u.department || '—'} • {u.role_name || 'No role'}</p>
                </div>
              </label>
            ))}
          </div>
          <div className="flex gap-3 justify-end">
            <Button
              onClick={() => { setApproverModalOpen(false); setSelectedApproverId(null); }}
              disabled={submitRequisition.isPending}
              className="px-4 py-2 border border-neutral-300 rounded-lg text-neutral-700 hover:bg-neutral-50"
            >
              Cancel
            </Button>
            <Button
              onClick={() => {
                if (!selectedApproverId) return;
                runAction(() =>
                  submitRequisition.mutate(
                    { orderId: order.id, approverId: selectedApproverId },
                    {
                      onSuccess: () => { setApproverModalOpen(false); setSelectedApproverId(null); },
                      onError: (err: any) => onError(err, 'Failed to submit requisition'),
                    }
                  )
                );
              }}
              disabled={submitRequisition.isPending || !selectedApproverId}
              className="px-4 py-2 bg-primary-600 text-white hover:bg-primary-700 flex items-center gap-2"
            >
              {submitRequisition.isPending && <Loader className="w-4 h-4 animate-spin" />}
              {submitRequisition.isPending ? 'Submitting...' : 'Submit to Approver'}
            </Button>
          </div>
        </Card>
      )}

      {/* Dispatch Challan Modal */}
      {dispatchModalOpen && (
        <Card className="border border-primary-300 bg-primary-50/30 p-6" padding="lg">
          <h3 className="text-lg font-semibold text-neutral-900 mb-2">Dispatch Order with Challan</h3>
          <p className="text-neutral-600 mb-4">
            Upload the dispatch challan before dispatching <strong>{order.order_number}</strong>.
          </p>

          <div className="space-y-4">
            <div>
              <label className={formLabel}>
                Dispatch Challan (PDF/Image)
              </label>
              <input
                ref={dispatchChallanRef}
                type="file"
                accept=".pdf,.jpg,.jpeg,.png"
                onChange={(e) => setDispatchChallanFile(e.target.files?.[0] || null)}
                className="block w-full text-sm text-neutral-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
              />
              {dispatchChallanFile && (
                <p className="text-xs text-success mt-1">✓ {dispatchChallanFile.name} selected</p>
              )}
            </div>

            {mySignature && (
              <div className="p-3 bg-neutral-50 rounded-lg border border-neutral-200">
                <p className="text-sm font-medium text-neutral-700 mb-2">
                  Your signature will be recorded with this dispatch:
                </p>
                <img
                  src={mySignature.signature_data}
                  alt="Your signature"
                  className="h-12 bg-white border border-neutral-200 rounded"
                />
                <p className="text-xs text-neutral-500 mt-1">
                  Signed by {currentUser?.full_name} on {formatDateTime(new Date().toISOString())}
                </p>
              </div>
            )}

            <div className="flex gap-3 justify-end">
              <Button
                onClick={() => setDispatchModalOpen(false)}
                disabled={uploadDocument.isPending || dispatchOrder.isPending}
                className="px-4 py-2 border border-neutral-300 rounded-lg text-neutral-700 hover:bg-neutral-50"
              >
                Cancel
              </Button>
              <Button
                onClick={handleDispatchWithChallan}
                disabled={uploadDocument.isPending || dispatchOrder.isPending}
                className="px-4 py-2 bg-primary-600 text-white hover:bg-primary-700 flex items-center gap-2 disabled:opacity-50"
              >
                {(uploadDocument.isPending || dispatchOrder.isPending) && (
                  <Loader className="w-4 h-4 animate-spin" />
                )}
                {uploadDocument.isPending
                  ? 'Uploading Challan...'
                  : dispatchOrder.isPending
                    ? 'Dispatching...'
                    : 'Confirm Dispatch'}
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Deliver Signed Challan Modal */}
      {deliverModalOpen && (
        <Card className="border border-success/40 bg-success/5 p-6" padding="lg">
          <h3 className="text-lg font-semibold text-neutral-900 mb-2">Mark Delivered with Signed Challan</h3>
          <p className="text-neutral-600 mb-4">
            Upload the signed delivery challan and verify the receiver's signature before marking{' '}
            <strong>{order.order_number}</strong> as delivered.
          </p>

          <div className="space-y-4">
            {/* Signed challan upload */}
            <div>
              <label className={formLabel}>
                Signed Delivery Challan (PDF/Image) *
              </label>
              <input
                ref={deliverChallanRef}
                type="file"
                accept=".pdf,.jpg,.jpeg,.png"
                onChange={(e) => setDeliverChallanFile(e.target.files?.[0] || null)}
                className="block w-full text-sm text-neutral-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-success/20 file:text-success hover:file:bg-success/30"
              />
              {deliverChallanFile && (
                <p className="text-xs text-success mt-1">✓ {deliverChallanFile.name} selected</p>
              )}
            </div>

            {/* Verification checklist */}
            <div className="p-4 bg-neutral-50 rounded-lg border border-neutral-200">
              <p className="text-sm font-semibold text-neutral-700 mb-3">
                Signature Verification Checklist
              </p>
              <label className="flex items-center gap-3 mb-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={signaturePresent}
                  onChange={(e) => setSignaturePresent(e.target.checked)}
                  className="w-4 h-4 rounded border-neutral-300 text-primary-600"
                />
                <span className="text-sm text-neutral-700">Receiver signature is present on the challan</span>
              </label>
              <label className="flex items-center gap-3 mb-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={datePresent}
                  onChange={(e) => setDatePresent(e.target.checked)}
                  className="w-4 h-4 rounded border-neutral-300 text-primary-600"
                />
                <span className="text-sm text-neutral-700">Delivery date is marked on the challan</span>
              </label>
              <label className="flex items-center gap-3 mb-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={receiverNamePresent}
                  onChange={(e) => setReceiverNamePresent(e.target.checked)}
                  className="w-4 h-4 rounded border-neutral-300 text-primary-600"
                />
                <span className="text-sm text-neutral-700">Receiver name is printed/written on the challan</span>
              </label>
              <hr className="my-3 border-neutral-200" />
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={verificationChecked}
                  onChange={(e) => setVerificationChecked(e.target.checked)}
                  className="w-4 h-4 rounded border-neutral-300 text-primary-600"
                />
                <span className="text-sm font-semibold text-neutral-800">
                  I have visually verified the receiver's signature matches the order details
                </span>
              </label>
            </div>

            {mySignature && (
              <div className="p-3 bg-neutral-50 rounded-lg border border-neutral-200">
                <p className="text-sm font-medium text-neutral-700 mb-2">
                  Your delivery confirmation signature:
                </p>
                <img
                  src={mySignature.signature_data}
                  alt="Your signature"
                  className="h-12 bg-white border border-neutral-200 rounded"
                />
                <p className="text-xs text-neutral-500 mt-1">
                  Verified by {currentUser?.full_name} on {formatDateTime(new Date().toISOString())}
                </p>
              </div>
            )}

            <div className="flex gap-3 justify-end">
              <Button
                onClick={() => setDeliverModalOpen(false)}
                disabled={uploadDocument.isPending || deliverOrder.isPending}
                className="px-4 py-2 border border-neutral-300 rounded-lg text-neutral-700 hover:bg-neutral-50"
              >
                Cancel
              </Button>
              <Button
                onClick={handleDeliverWithChallan}
                disabled={
                  uploadDocument.isPending ||
                  deliverOrder.isPending ||
                  !verificationChecked ||
                  !deliverChallanFile
                }
                className="px-4 py-2 bg-success text-white hover:bg-success/90 flex items-center gap-2 disabled:opacity-50"
              >
                {(uploadDocument.isPending || deliverOrder.isPending) && (
                  <Loader className="w-4 h-4 animate-spin" />
                )}
                {uploadDocument.isPending
                  ? 'Uploading Challan...'
                  : deliverOrder.isPending
                    ? 'Confirming Delivery...'
                    : 'Confirm Delivery'}
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Order Info */}
      <Card padding="lg">
        <h2 className="text-lg font-semibold text-neutral-900 mb-4">Order Information</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <p className="text-sm text-neutral-600 font-medium mb-1">Vendor</p>
            <p className="text-neutral-900">{vendor?.name || `Vendor #${order.vendor_id}`}</p>
            {vendor?.contact_person && (
              <p className="text-sm text-neutral-500">Contact: {vendor.contact_person}</p>
            )}
          </div>
          <div>
            <p className="text-sm text-neutral-600 font-medium mb-1">Created By</p>
            <p className="text-neutral-900">{userLabel(order.created_by)}</p>
            <p className="text-sm text-neutral-500">
              {formatDateTime(order.created_at)}
            </p>
          </div>
          <div>
            <p className="text-sm text-neutral-600 font-medium mb-1">Delivery Address</p>
            <p className="text-neutral-900">{order.delivery_address || '—'}</p>
          </div>
          <div>
            <p className="text-sm text-neutral-600 font-medium mb-1">Remarks</p>
            <p className="text-neutral-900">{order.remarks || '—'}</p>
          </div>
        </div>
      </Card>

      {/* Documents */}
      {documents && documents.length > 0 && (
        <Card padding="lg">
          <h2 className="text-lg font-semibold text-neutral-900 mb-4">Documents</h2>
          <div className="space-y-2">
            {documents.map((doc: any) => (
              <div
                key={doc.id}
                className="flex items-center justify-between p-3 bg-neutral-50 rounded-lg border border-neutral-100"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-neutral-900 truncate">{doc.file_name}</p>
                  <p className="text-xs text-neutral-500">
                    {doc.doc_category?.replace(/_/g, ' ')} • v{doc.version} •{' '}
                    {formatDateTime(doc.uploaded_at)}
                  </p>
                </div>
                <Button
                  variant="secondary"
                  onClick={() => {
                    downloadDocument.mutate(doc.id, {
                      onSuccess: (blob) => {
                        const url = URL.createObjectURL(blob);
                        window.open(url, '_blank');
                        setTimeout(() => URL.revokeObjectURL(url), 60000);
                      },
                      onError: () => toast.error('Failed to download document'),
                    });
                  }}
                  disabled={downloadDocument.isPending}
                  className="ml-3 flex items-center gap-1 flex-shrink-0"
                  size="sm"
                >
                  {downloadDocument.isPending ? (
                    <Loader className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Eye className="w-3.5 h-3.5" />
                  )}
                  View
                </Button>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Requisition History */}
      {order.status !== 'draft' && (
        <Card padding="lg">
          <h2 className="text-lg font-semibold text-neutral-900 mb-4">Requisition History</h2>
          <div className="space-y-3">
            {(() => {
              const reqTimeline = timeline.filter((t: any) =>
                ['requisition_generated', 'signed_uploaded', 'approved'].includes(t.action)
              );
              if (reqTimeline.length === 0) {
                return <p className="text-neutral-500 text-center py-4">No requisition history</p>;
              }
              const actionLabels: Record<string, string> = {
                requisition_generated: 'Requisition Submitted',
                signed_uploaded: 'Signed Requisition Uploaded',
                approved: 'Approved',
              };
              return reqTimeline.map((entry: any) => {
                const relatedDocs = (documents ?? []).filter(
                  (d: any) =>
                    (entry.action === 'requisition_generated' && d.doc_category === 'requisition') ||
                    (entry.action === 'signed_uploaded' && d.doc_category === 'signed_requisition')
                );
                return (
                  <div
                    key={entry.id}
                    className="flex items-start gap-3 p-3 bg-neutral-50 rounded-lg border border-neutral-100"
                  >
                    <div
                      className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${
                        entry.action === 'approved' ? 'bg-success' : 'bg-primary-600'
                      }`}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between flex-wrap gap-1">
                        <p className="font-medium text-neutral-900">
                          {actionLabels[entry.action] || entry.action}
                        </p>
                        <span className="text-xs text-neutral-500">
                          {formatDateTime(entry.created_at)}
                        </span>
                      </div>
                      <p className="text-sm text-neutral-600">
                        by {userLabel(entry.user_id)}
                        {entry.comments && ` - ${entry.comments}`}
                      </p>
                      {relatedDocs.length > 0 && (
                        <div className="flex flex-wrap gap-2 mt-2">
                          {relatedDocs.map((doc: any) => (
                            <button
                              key={doc.id}
                              onClick={() => {
                                downloadDocument.mutate(doc.id, {
                                  onSuccess: (blob) => {
                                    const url = URL.createObjectURL(blob);
                                    window.open(url, '_blank');
                                    setTimeout(() => URL.revokeObjectURL(url), 60000);
                                  },
                                  onError: () => toast.error('Failed to load document'),
                                });
                              }}
                              className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium bg-white border border-neutral-200 rounded-md text-primary-600 hover:bg-primary-50 hover:border-primary-300 transition-colors"
                            >
                              View{' '}
                              {doc.doc_category === 'signed_requisition'
                                ? 'Signed PDF'
                                : 'Requisition PDF'}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                );
              });
            })()}
          </div>
        </Card>
      )}

      {/* Items */}
      <Card padding="lg">
        <h2 className="text-lg font-semibold text-neutral-900 mb-4">Items</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-neutral-200">
                <th className="text-left py-2 px-3 font-semibold text-neutral-700">Item</th>
                <th className="text-left py-2 px-3 font-semibold text-neutral-700">SKU</th>
                <th className="text-right py-2 px-3 font-semibold text-neutral-700">Ordered</th>
                <th className="text-right py-2 px-3 font-semibold text-neutral-700">Reserved</th>
                <th className="text-right py-2 px-3 font-semibold text-neutral-700">Dispatched</th>
              </tr>
            </thead>
            <tbody>
              {order.items.map((orderItem: any) => {
                const info = itemMap[orderItem.item_id];
                return (
                  <tr key={orderItem.id} className="border-b border-neutral-100">
                    <td className="py-2 px-3">
                      <button
                        onClick={() => navigate(`/inventory/${orderItem.item_id}`)}
                        className="text-primary-600 hover:underline text-left"
                      >
                        {info?.name || `Item #${orderItem.item_id}`}
                      </button>
                    </td>
                    <td className="py-2 px-3 font-mono text-neutral-600">{info?.sku || '—'}</td>
                    <td className="py-2 px-3 text-right text-neutral-900">
                      {Number(orderItem.quantity_ordered)}
                    </td>
                    <td className="py-2 px-3 text-right text-neutral-900">
                      {Number(orderItem.quantity_reserved)}
                    </td>
                    <td className="py-2 px-3 text-right text-neutral-900">
                      {Number(orderItem.quantity_dispatched)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-neutral-500 mt-3">
          Reserved = stock held for this order after approval. Dispatched = stock deducted from
          inventory when the order ships.
        </p>
      </Card>

      {/* Timeline */}
      <Card padding="lg">
        <h2 className="text-lg font-semibold text-neutral-900 mb-4">Timeline</h2>
        {timeline.length === 0 ? (
          <p className="text-neutral-500 text-center py-6">No timeline entries</p>
        ) : (
          <div className="space-y-3">
            {timeline.map((entry: any) => {
              const actionDocCategory: Record<string, string> = {
                dispatched: 'dispatch_challan',
                delivered: 'signed_delivery_challan',
                signed_requisition_uploaded: 'signed_requisition',
              };
              const relatedDocs = (documents ?? []).filter(
                (d: any) => d.doc_category === actionDocCategory[entry.action]
              );
              return (
                <div
                  key={entry.id}
                  className="flex items-start gap-3 p-3 bg-neutral-50 rounded-lg border border-neutral-100"
                >
                  <div className="w-2 h-2 rounded-full bg-primary-600 mt-2 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between flex-wrap gap-1">
                      <p className="font-medium text-neutral-900">{formatStatus(entry.action)}</p>
                      <span className="text-xs text-neutral-500">
                        {formatDateTime(entry.created_at)}
                      </span>
                    </div>
                    <p className="text-sm text-neutral-600">
                      by {userLabel(entry.user_id)}
                      {entry.comments && ` — ${entry.comments}`}
                    </p>
                    {relatedDocs.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-2">
                        {relatedDocs.map((doc: any) => (
                          <button
                            key={doc.id}
                            onClick={() => {
                              downloadDocument.mutate(doc.id, {
                                onSuccess: (blob) => {
                                  const url = URL.createObjectURL(blob);
                                  window.open(url, '_blank');
                                  setTimeout(() => URL.revokeObjectURL(url), 60000);
                                },
                                onError: () => toast.error('Failed to load document'),
                              });
                            }}
                            className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium bg-white border border-neutral-200 rounded-md text-primary-600 hover:bg-primary-50 hover:border-primary-300 transition-colors"
                          >
                            <Eye className="w-3 h-3" />
                            {doc.doc_category === 'dispatch_challan'
                              ? 'Dispatch Challan'
                              : doc.doc_category === 'signed_delivery_challan'
                                ? 'Signed Challan'
                                : doc.file_name}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card>

      {/* Digital Signature Info */}
      {mySignature && (
        <Card padding="lg">
          <h2 className="text-lg font-semibold text-neutral-900 mb-4">
            <Eye className="w-5 h-5 inline mr-2 text-primary-600" />
            Your Digital Signature
          </h2>
          <p className="text-sm text-neutral-600 mb-3">
            This signature will be recorded on all approvals and verifications you perform.
          </p>
          <div className="p-4 bg-neutral-50 rounded-lg border border-neutral-200 inline-block">
            <img
              src={mySignature.signature_data}
              alt="Your digital signature"
              className="h-16 bg-white border border-neutral-200 rounded"
            />
            <p className="text-xs text-neutral-500 mt-1">
              {currentUser?.full_name} • {currentUser?.email}
            </p>
          </div>
        </Card>
      )}

      {cropFile && (
        <ImageCropModal
          file={cropFile}
          onConfirm={handleCropConfirm}
          onCancel={() => setCropFile(null)}
        />
      )}
    </div>
  );
};

export default OrderDetailPage;
