import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Card, Button, ListLoadingState, StatusBadge } from '../../components/ui';
import { cardErrorPadded, formLabel } from '../../styles/classNames';
import { EntityListCard } from '../../components/common/EntityListCard';
import { formatDate, formatDateTime } from '../../utils/format';
import { ArrowLeft, Edit2, Trash2, Plus, AlertCircle, SlidersHorizontal } from 'lucide-react';
import {
  useInventoryItem,
  useUpdateInventoryItem,
  useDeleteInventoryItem,
  useRestockItem,
  useAdjustItem,
} from '../../hooks/useInventory';
import { useUserNameMap } from '../../hooks/useUsers';

const getApiError = (error: any, fallback: string): string => {
  const detail = error?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (detail?.message) {
    const extra = Array.isArray(detail.errors) ? ` ${detail.errors.join('; ')}` : '';
    return `${detail.message}.${extra}`;
  }
  return error?.message || fallback;
};

export const InventoryDetailPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const itemId = id ? parseInt(id) : null;

  const { data: item, isLoading, error } = useInventoryItem(itemId);
  const { mutate: updateItem, isPending: isUpdating } = useUpdateInventoryItem();
  const { mutate: deleteItem, isPending: isDeleting } = useDeleteInventoryItem();
  const { mutate: restockItem, isPending: isRestocking } = useRestockItem();
  const { mutate: adjustItem, isPending: isAdjusting } = useAdjustItem();
  const userNames = useUserNameMap();

  const [isEditMode, setIsEditMode] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const [formError, setFormError] = useState('');
  const [editForm, setEditForm] = useState({ name: '', description: '', minimum_quantity: 0 });

  // Restock / Adjust forms
  const [stockAction, setStockAction] = useState<'restock' | 'adjust' | null>(null);
  const [stockQty, setStockQty] = useState('');
  const [stockReason, setStockReason] = useState('');

  const startEdit = () => {
    if (!item) return;
    setEditForm({
      name: item.name,
      description: item.description || '',
      minimum_quantity: Number(item.minimum_quantity),
    });
    setFormError('');
    setIsEditMode(true);
  };

  const handleUpdate = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');
    if (!itemId) return;
    if (!editForm.name.trim()) {
      setFormError('Item name is required');
      return;
    }

    updateItem(
      {
        itemId,
        data: {
          name: editForm.name,
          description: editForm.description || undefined,
          minimum_quantity: editForm.minimum_quantity,
        },
      },
      {
        onSuccess: () => setIsEditMode(false),
        onError: (err: any) => setFormError(getApiError(err, 'Failed to update item')),
      }
    );
  };

  const handleDelete = () => {
    if (!itemId) return;
    deleteItem(itemId, {
      onSuccess: () => navigate('/inventory'),
      onError: (err: any) => {
        setFormError(getApiError(err, 'Failed to delete item'));
        setDeleteConfirm(false);
      },
    });
  };

  const handleStockSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');
    if (!itemId || !stockAction) return;

    const qty = parseFloat(stockQty);
    if (isNaN(qty) || (stockAction === 'restock' && qty <= 0) || (stockAction === 'adjust' && qty < 0)) {
      setFormError(
        stockAction === 'restock'
          ? 'Quantity to add must be greater than 0'
          : 'New quantity must be 0 or greater'
      );
      return;
    }
    if (!stockReason.trim()) {
      setFormError('Reason is required');
      return;
    }

    const onSuccess = () => {
      setStockAction(null);
      setStockQty('');
      setStockReason('');
    };
    const onError = (err: any) => setFormError(getApiError(err, 'Stock update failed'));

    if (stockAction === 'restock') {
      restockItem({ item_id: itemId, quantity: qty, reason: stockReason }, { onSuccess, onError });
    } else {
      adjustItem({ item_id: itemId, new_quantity: qty, reason: stockReason }, { onSuccess, onError });
    }
  };

  if (isLoading) return <ListLoadingState message="Loading item..." />;

  if (error || !item) {
    return (
      <div className="space-y-6 pb-6">
        <button
          onClick={() => navigate('/inventory')}
          className="p-2 hover:bg-neutral-100 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5 text-neutral-600" />
        </button>
        <Card className={cardErrorPadded} padding="lg">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-error flex-shrink-0" />
            <p className="text-error">
              {error instanceof Error ? error.message : 'Item not found'}
            </p>
          </div>
        </Card>
      </div>
    );
  }

  const currentQty = Number(item.current_quantity);
  const reservedQty = Number(item.reserved_quantity);
  const availableQty = currentQty - reservedQty;
  const minQty = Number(item.minimum_quantity);
  const transactions = item.transactions ?? [];

  return (
    <div className="space-y-6 pb-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-4">
          <button
            onClick={() => navigate('/inventory')}
            className="p-2 hover:bg-neutral-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-neutral-700" />
          </button>
          <div>
            <h1 className="text-3xl font-bold text-neutral-900">{item.name}</h1>
            <p className="text-neutral-600 mt-1">
              SKU: {item.sku}
              {item.barcode && <span className="ml-3">Barcode: {item.barcode}</span>}
            </p>
          </div>
        </div>
        {!isEditMode && (
          <div className="flex gap-2">
            <Button
              onClick={startEdit}
              className="flex items-center gap-2 bg-primary-600 text-white hover:bg-primary-700"
            >
              <Edit2 className="w-4 h-4" />
              Edit
            </Button>
            <Button
              onClick={() => setDeleteConfirm(true)}
              className="flex items-center gap-2 bg-error/10 text-error hover:bg-error/20"
            >
              <Trash2 className="w-4 h-4" />
              Delete
            </Button>
          </div>
        )}
      </div>

      {/* Error Banner */}
      {formError && (
        <Card className={cardErrorPadded} padding="lg">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-error flex-shrink-0" />
            <p className="text-error">{formError}</p>
          </div>
        </Card>
      )}

      {/* Delete Confirmation */}
      {deleteConfirm && (
        <Card className="border border-error bg-error/5 p-6" padding="lg">
          <h3 className="text-lg font-semibold text-neutral-900 mb-2">Delete Item?</h3>
          <p className="text-neutral-600 mb-4">
            This action cannot be undone. Are you sure you want to delete{' '}
            <strong>{item.name}</strong>?
          </p>
          <div className="flex gap-3 justify-end">
            <Button
              onClick={() => setDeleteConfirm(false)}
              disabled={isDeleting}
              className="px-4 py-2 border border-neutral-300 rounded-lg text-neutral-700 hover:bg-neutral-50"
            >
              Cancel
            </Button>
            <Button
              onClick={handleDelete}
              disabled={isDeleting}
              className="px-4 py-2 bg-error text-white hover:bg-error/90 flex items-center gap-2"
            >
              {isDeleting && <Loader className="w-4 h-4 animate-spin" />}
              {isDeleting ? 'Deleting...' : 'Delete'}
            </Button>
          </div>
        </Card>
      )}

      {/* Edit Form */}
      {isEditMode ? (
        <Card padding="lg">
          <h2 className="text-lg font-semibold text-neutral-900 mb-4">Edit Item</h2>
          <form onSubmit={handleUpdate} className="space-y-4">
            <div>
              <label className={formLabel}>Item Name *</label>
              <input
                type="text"
                value={editForm.name}
                onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                disabled={isUpdating}
              />
            </div>
            <div>
              <label className={formLabel}>Description</label>
              <textarea
                value={editForm.description}
                onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                rows={3}
                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                disabled={isUpdating}
              />
            </div>
            <div className="max-w-xs">
              <label className={formLabel}>
                Minimum Quantity
              </label>
              <input
                type="number"
                min={0}
                value={editForm.minimum_quantity}
                onChange={(e) =>
                  setEditForm({ ...editForm, minimum_quantity: Number(e.target.value) })
                }
                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                disabled={isUpdating}
              />
            </div>
            <div className="flex gap-2 justify-end">
              <Button
                type="button"
                onClick={() => setIsEditMode(false)}
                disabled={isUpdating}
                className="px-4 py-2 border border-neutral-300 rounded-lg text-neutral-700 hover:bg-neutral-50"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={isUpdating}
                className="px-4 py-2 bg-primary-600 text-white hover:bg-primary-700 flex items-center gap-2"
              >
                {isUpdating && <Loader className="w-4 h-4 animate-spin" />}
                {isUpdating ? 'Saving...' : 'Save Changes'}
              </Button>
            </div>
          </form>
        </Card>
      ) : (
        <>
          {/* Key Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card padding="lg">
              <p className="text-sm text-neutral-600 font-medium">Current Quantity</p>
              <p
                className={`text-3xl font-bold mt-2 ${
                  currentQty === 0
                    ? 'text-error'
                    : currentQty <= minQty
                      ? 'text-warning'
                      : 'text-neutral-900'
                }`}
              >
                {currentQty}
              </p>
              <p className="text-xs text-neutral-500 mt-1">Min: {minQty}</p>
            </Card>
            <Card padding="lg">
              <p className="text-sm text-neutral-600 font-medium">Reserved</p>
              <p className="text-3xl font-bold text-neutral-900 mt-2">{reservedQty}</p>
              <p className="text-xs text-neutral-500 mt-1">Held for approved orders</p>
            </Card>
            <Card padding="lg">
              <p className="text-sm text-neutral-600 font-medium">Available</p>
              <p className="text-3xl font-bold text-neutral-900 mt-2">{availableQty}</p>
              <p className="text-xs text-neutral-500 mt-1">Current − reserved</p>
            </Card>
            <Card padding="lg">
              <p className="text-sm text-neutral-600 font-medium">Type</p>
              <p className="text-3xl font-bold text-neutral-900 mt-2 capitalize">
                {item.item_type}
              </p>
              <p className="text-xs text-neutral-500 mt-1">Item classification</p>
            </Card>
          </div>

          {/* Details */}
          <Card padding="lg">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <p className="text-sm text-neutral-600 font-medium mb-1">SKU</p>
                <p className="text-neutral-900 font-mono">{item.sku}</p>
              </div>
              <div>
                <p className="text-sm text-neutral-600 font-medium mb-1">Created</p>
                <p className="text-neutral-900">
                  {formatDate(item.created_at)}
                </p>
              </div>
              <div className="md:col-span-2">
                <p className="text-sm text-neutral-600 font-medium mb-1">Description</p>
                <p className="text-neutral-900">{item.description || '—'}</p>
              </div>
            </div>
          </Card>

          {/* Stock Actions */}
          <Card padding="lg">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-neutral-900">Stock Transactions</h3>
              <div className="flex gap-2">
                <Button
                  onClick={() => {
                    setStockAction(stockAction === 'restock' ? null : 'restock');
                    setStockQty('');
                    setStockReason('');
                    setFormError('');
                  }}
                  className="flex items-center gap-2 bg-primary-600 text-white hover:bg-primary-700 text-sm"
                >
                  <Plus className="w-4 h-4" />
                  Restock
                </Button>
                <Button
                  onClick={() => {
                    setStockAction(stockAction === 'adjust' ? null : 'adjust');
                    setStockQty('');
                    setStockReason('');
                    setFormError('');
                  }}
                  className="flex items-center gap-2 border border-neutral-300 text-neutral-700 hover:bg-neutral-50 text-sm"
                >
                  <SlidersHorizontal className="w-4 h-4" />
                  Adjust
                </Button>
              </div>
            </div>

            {stockAction && (
              <form
                onSubmit={handleStockSubmit}
                className="mb-6 p-4 bg-neutral-50 rounded-lg border border-neutral-200 space-y-3"
              >
                <p className="text-sm font-medium text-neutral-700">
                  {stockAction === 'restock'
                    ? 'Add stock (quantity to add)'
                    : 'Adjust stock (set new total quantity)'}
                </p>
                <div className="flex flex-wrap gap-2">
                  <input
                    type="number"
                    step="any"
                    placeholder={stockAction === 'restock' ? 'Quantity to add' : 'New quantity'}
                    value={stockQty}
                    onChange={(e) => setStockQty(e.target.value)}
                    className="w-40 px-3 py-2 border border-neutral-300 rounded-lg text-sm"
                    disabled={isRestocking || isAdjusting}
                  />
                  <input
                    type="text"
                    placeholder="Reason (required)"
                    value={stockReason}
                    onChange={(e) => setStockReason(e.target.value)}
                    className="flex-1 min-w-48 px-3 py-2 border border-neutral-300 rounded-lg text-sm"
                    disabled={isRestocking || isAdjusting}
                  />
                  <Button
                    type="submit"
                    disabled={isRestocking || isAdjusting}
                    className="px-4 py-2 bg-primary-600 text-white hover:bg-primary-700 text-sm flex items-center gap-2"
                  >
                    {(isRestocking || isAdjusting) && <Loader className="w-4 h-4 animate-spin" />}
                    {stockAction === 'restock' ? 'Add Stock' : 'Set Quantity'}
                  </Button>
                </div>
              </form>
            )}

            {transactions.length === 0 ? (
              <p className="text-neutral-500 text-center py-8">No transactions yet</p>
            ) : (
              <div className="space-y-2">
                {transactions.map((tx) => (
                  <EntityListCard
                    key={tx.id}
                    title={`${Number(tx.change_quantity) > 0 ? '+' : ''}${Number(tx.change_quantity)} units (${Number(tx.previous_quantity)} → ${Number(tx.new_quantity)})`}
                    subtitle={`${tx.transaction_type.toUpperCase()}${tx.reference_type ? ` • ${tx.reference_type} #${tx.reference_id}` : ''}`}
                    description={`${formatDateTime(tx.created_at)}${tx.reason ? ` • ${tx.reason}` : ''}${tx.created_by ? ` • by ${userNames[tx.created_by] || `User #${tx.created_by}`}` : ''}`}
                    trailing={
                      <StatusBadge status={tx.transaction_type}>{tx.transaction_type.toUpperCase()}</StatusBadge>
                    }
                  />
                ))}
              </div>
            )}
          </Card>
        </>
      )}
    </div>
  );
};

export default InventoryDetailPage;
