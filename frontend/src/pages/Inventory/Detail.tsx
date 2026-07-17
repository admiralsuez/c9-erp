import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Card, Button, ListLoadingState, StatusBadge } from '../../components/ui';
import { cardErrorPadded, formLabel } from '../../styles/classNames';
import { EntityListCard } from '../../components/common/EntityListCard';
import { formatDate, formatDateTime } from '../../utils/format';
import { ArrowLeft, Edit2, Trash2, Plus, AlertCircle, SlidersHorizontal, Loader, Barcode, Info } from 'lucide-react';
import { SerialNumberInput } from '../../components/inventory/SerialNumberInput';
import { SerialNumberImport } from '../../components/inventory/SerialNumberImport';
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

  const { data: item, isLoading, error, refetch } = useInventoryItem(itemId);
  const { mutate: updateItem, isPending: isUpdating } = useUpdateInventoryItem();
  const { mutate: deleteItem, isPending: isDeleting } = useDeleteInventoryItem();
  const { mutate: restockItem, isPending: isRestocking } = useRestockItem();
  const { mutate: adjustItem, isPending: isAdjusting } = useAdjustItem();
  const userNames = useUserNameMap();

  const [isEditMode, setIsEditMode] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const [formError, setFormError] = useState('');
  const [editForm, setEditForm] = useState({
    name: '',
    sku: '',
    barcode: '',
    category_id: 0,
    item_type: 'consumable',
    description: '',
    minimum_quantity: 0,
    opening_quantity: 0,
  });
  const [showSerialMgmt, setShowSerialMgmt] = useState(false);
  const [serialMgmtMode, setSerialMgmtMode] = useState<'generate' | 'import'>('import');
  const [categories, setCategories] = useState(['Furniture', 'Supplies', 'Lighting', 'Electronics', 'Tools']);
  const [showAddCategory, setShowAddCategory] = useState(false);
  const [newCategory, setNewCategory] = useState('');
  const [notifyLowStock, setNotifyLowStock] = useState(false);

  // Restock / Adjust forms
  const [stockAction, setStockAction] = useState<'restock' | 'adjust' | null>(null);
  const [stockQty, setStockQty] = useState('');
  const [stockReason, setStockReason] = useState('');

  const startEdit = () => {
    if (!item) return;
    setEditForm({
      name: item.name,
      sku: item.sku,
      barcode: item.barcode || '',
      category_id: item.category_id || 0,
      item_type: item.item_type || 'consumable',
      description: item.description || '',
      minimum_quantity: Number(item.minimum_quantity),
      opening_quantity: Number(item.current_quantity),
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
    if (!editForm.sku.trim()) {
      setFormError('SKU is required');
      return;
    }

    updateItem(
      {
        itemId,
        data: {
          name: editForm.name,
          category_id: editForm.category_id || undefined,
          item_type: editForm.item_type,
          barcode: editForm.barcode || undefined,
          description: editForm.description || undefined,
          minimum_quantity: editForm.minimum_quantity,
          current_quantity: editForm.opening_quantity,
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

  const children = item.children ?? [];
  const isParent = children.length > 0;
  const currentQty = isParent
    ? children.reduce((sum: number, c: any) => sum + Number(c.current_quantity), 0)
    : Number(item.current_quantity);
  const reservedQty = isParent
    ? children.reduce((sum: number, c: any) => sum + Number(c.reserved_quantity), 0)
    : Number(item.reserved_quantity);
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
              onClick={() => setShowSerialMgmt(true)}
              className="flex items-center gap-2 bg-blue-600 text-white hover:bg-blue-700"
            >
              <Barcode className="w-4 h-4" />
              Manage Serials
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

      {/* Child Variants (shown when item is a parent) */}
      {!isEditMode && item.children && item.children.length > 0 && (
        <Card padding="lg">
          <h2 className="text-lg font-semibold text-neutral-900 mb-4">
            Child Variants ({item.children.length})
          </h2>
          <div className="space-y-2">
            {item.children.map((child) => (
              <div
                key={child.id}
                className="flex items-center justify-between p-3 bg-neutral-50 rounded-lg border border-neutral-200 hover:border-primary-300 transition-colors cursor-pointer"
                onClick={() => navigate(`/inventory/${child.id}`)}
              >
                <div className="flex-1">
                  <p className="font-medium text-neutral-900 text-sm">{child.name}</p>
                  <p className="text-xs text-neutral-500">SKU: {child.sku}</p>
                  {child.description && (
                    <p className="text-xs text-neutral-600 mt-1">{child.description}</p>
                  )}
                </div>
                <div className="flex items-center gap-3 text-right">
                  <div>
                    <p className="font-semibold text-neutral-900 text-sm">{Number(child.current_quantity)}</p>
                    <p className="text-xs text-neutral-500">qty</p>
                  </div>
                  <button
                    type="button"
                    onClick={(e) => { e.stopPropagation(); navigate(`/inventory/${child.id}`); }}
                    className="px-3 py-1.5 text-xs bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition"
                  >
                    View
                  </button>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Edit Form */}
      {isEditMode ? (
        <Card padding="lg">
          <h2 className="text-lg font-semibold text-neutral-900 mb-4">Edit Item</h2>
          <form onSubmit={handleUpdate} className="space-y-6">
            {/* Section 1: Item Identity */}
            <div className="space-y-4">
              <h3 className="text-md font-medium text-neutral-900">Item Identity</h3>
              <div>
                <label className={formLabel}>Item Name *</label>
                <input
                  type="text"
                  value={editForm.name}
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                  placeholder="e.g., Office Chair"
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  disabled={isUpdating}
                />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className={formLabel}>SKU (Stock Keeping Unit) *</label>
                  <input
                    type="text"
                    value={editForm.sku}
                    onChange={(e) => setEditForm({ ...editForm, sku: e.target.value })}
                    placeholder="e.g., OFC-001"
                    className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    disabled={isUpdating}
                  />
                </div>
                <div>
                  <label className={formLabel}>Barcode (Optional)</label>
                  <input
                    type="text"
                    value={editForm.barcode}
                    onChange={(e) => setEditForm({ ...editForm, barcode: e.target.value })}
                    placeholder="e.g., 1234567890"
                    className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    disabled={isUpdating}
                  />
                </div>
              </div>
              <div>
                <label className={formLabel}>Description</label>
                <textarea
                  value={editForm.description}
                  onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                  placeholder="Detailed description of the item..."
                  rows={3}
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  disabled={isUpdating}
                />
              </div>
            </div>

            {/* Section 2: Classification */}
            <div className="space-y-4">
              <h3 className="text-md font-medium text-neutral-900">Classification</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className={formLabel}>Category</label>
                  <div className="flex gap-2">
                    <select
                      value={editForm.category_id}
                      onChange={(e) => setEditForm({ ...editForm, category_id: Number(e.target.value) })}
                      className="flex-1 px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      disabled={isUpdating}
                    >
                      <option value="0">Select Category</option>
                      {categories.map((cat, idx) => (
                        <option key={idx} value={idx + 1}>
                          {cat}
                        </option>
                      ))}
                    </select>
                    <button
                      type="button"
                      onClick={() => setShowAddCategory(!showAddCategory)}
                      className="px-3 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition disabled:bg-gray-400"
                      disabled={isUpdating}
                      title="Add new category"
                    >
                      <Plus size={18} />
                    </button>
                  </div>
                </div>
                <div>
                  <label className={formLabel}>Item Type</label>
                  <select
                    value={editForm.item_type}
                    onChange={(e) => setEditForm({ ...editForm, item_type: e.target.value as any })}
                    className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    disabled={isUpdating}
                  >
                    <option value="consumable">Consumable (Single-use)</option>
                    <option value="returnable">Returnable (Multi-use)</option>
                  </select>
                </div>
              </div>
              {showAddCategory && (
                <div className="p-3 bg-neutral-50 border border-neutral-200 rounded-lg space-y-2">
                  <input
                    type="text"
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        if (newCategory.trim() && !categories.includes(newCategory)) {
                          setCategories([...categories, newCategory]);
                          setNewCategory('');
                          setShowAddCategory(false);
                        }
                      }
                    }}
                    placeholder="Enter new category name"
                    className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    disabled={isUpdating}
                    autoFocus
                  />
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      onClick={() => {
                        if (newCategory.trim() && !categories.includes(newCategory)) {
                          setCategories([...categories, newCategory]);
                          setNewCategory('');
                          setShowAddCategory(false);
                        }
                      }}
                      disabled={isUpdating}
                      className="flex-1 px-3 py-1 bg-primary-600 text-white rounded text-sm hover:bg-primary-700"
                    >
                      Add Category
                    </Button>
                    <Button
                      type="button"
                      onClick={() => {
                        setShowAddCategory(false);
                        setNewCategory('');
                      }}
                      disabled={isUpdating}
                      className="flex-1 px-3 py-1 border border-neutral-300 text-neutral-700 rounded text-sm hover:bg-neutral-50"
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              )}
            </div>

            {/* Section 3: Stock Management */}
            <div className="space-y-4">
              <h3 className="text-md font-medium text-neutral-900">Stock Management</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className={formLabel}>Available Quantity</label>
                  <p className="text-xs text-neutral-500 mb-1">Initial stock level for this item</p>
                  <input
                    type="number"
                    min="0"
                    value={editForm.opening_quantity}
                    onChange={(e) => setEditForm({ ...editForm, opening_quantity: Number(e.target.value) })}
                    className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    disabled={isUpdating}
                  />
                </div>
                <div>
                  <label className={formLabel}>Safety Stock</label>
                  <p className="text-xs text-neutral-500 mb-1">Minimum stock level to maintain</p>
                  <input
                    type="number"
                    min="0"
                    value={editForm.minimum_quantity}
                    onChange={(e) => setEditForm({ ...editForm, minimum_quantity: Number(e.target.value) })}
                    className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                    disabled={isUpdating}
                  />
                </div>
              </div>
              <div>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={notifyLowStock}
                    onChange={(e) => setNotifyLowStock(e.target.checked)}
                    className="w-4 h-4 rounded border-neutral-300"
                    disabled={isUpdating}
                  />
                  <span className="text-sm text-neutral-700">Notify me when stock falls below safety stock</span>
                </label>
              </div>
            </div>

            <div className="flex gap-2 justify-end pt-4 border-t border-neutral-200">
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

          {/* Serial Management Modal */}
          {showSerialMgmt && (
            <Card padding="lg" className="border-2 border-blue-500">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-neutral-900">Manage Serial Numbers</h2>
                <button
                  onClick={() => {
                    setShowSerialMgmt(false);
                    setSerialMgmtMode('import');
                  }}
                  className="text-gray-500 hover:text-gray-700 text-2xl leading-none"
                >
                  ×
                </button>
              </div>

              {/* Enable/Disable Serial Tracking */}
              <div className="mb-6 p-4 bg-neutral-50 border border-neutral-200 rounded-lg">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={serialMgmtMode === 'generate'}
                    onChange={() => setSerialMgmtMode(serialMgmtMode === 'generate' ? 'import' : 'generate')}
                    className="w-5 h-5 rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
                  />
                  <div>
                    <span className="font-medium text-neutral-900">Generate serial numbers automatically</span>
                    <span className="ml-1 group relative inline-block">
                      <Info className="w-3.5 h-3.5 text-neutral-400 inline cursor-help align-text-bottom" />
                      <span className="invisible group-hover:visible absolute left-0 top-full mt-1 w-64 p-2 bg-neutral-800 text-white text-xs rounded shadow-lg z-10">
                        Check this if you want the system to generate serial numbers. Uncheck to manually enter or import existing manufacturer serials.
                      </span>
                    </span>
                    <p className="text-xs text-neutral-500 mt-0.5">
                      {serialMgmtMode === 'generate'
                        ? 'System will auto-generate serial numbers based on your settings below'
                        : 'Enter serial numbers that your units already have (manufacturer serials)'}
                    </p>
                  </div>
                </label>
              </div>

              {/* Generate Mode */}
              {serialMgmtMode === 'generate' && itemId && (
                <SerialNumberInput
                  itemId={itemId}
                  onSerialsGenerated={() => {
                    refetch();
                  }}
                  disabled={false}
                />
              )}

              {/* Import Mode */}
              {serialMgmtMode !== 'generate' && itemId && (
                <SerialNumberImport
                  itemId={itemId}
                  onSerialsImported={() => {
                    refetch();
                  }}
                  disabled={false}
                />
              )}
            </Card>
          )}

          {/* Item Images */}
          {item.image_url && (
            <Card padding="lg">
              <h3 className="text-lg font-semibold text-neutral-900 mb-4">Item Images</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-neutral-600 font-medium mb-2 capitalize">Image</p>
                  <img
                    src={item.image_url}
                    alt={item.name}
                    className="w-full h-48 object-cover rounded-lg border border-neutral-200"
                  />
                </div>
              </div>
            </Card>
          )}

          {/* Serial Numbers */}
          {item.serial_numbers && item.serial_numbers.length > 0 && (
            <Card padding="lg">
              <h3 className="text-lg font-semibold text-neutral-900 mb-4">
                Serial Numbers ({item.serial_numbers.length})
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-neutral-200">
                      <th className="text-left px-4 py-2 font-medium text-neutral-700">Serial Number</th>
                      <th className="text-left px-4 py-2 font-medium text-neutral-700">Batch ID</th>
                      <th className="text-left px-4 py-2 font-medium text-neutral-700">Condition</th>
                      <th className="text-left px-4 py-2 font-medium text-neutral-700">Assigned Order</th>
                      <th className="text-left px-4 py-2 font-medium text-neutral-700">Created</th>
                    </tr>
                  </thead>
                  <tbody>
                    {item.serial_numbers.map((serial: any) => (
                      <tr key={serial.id} className="border-b border-neutral-200 hover:bg-neutral-50">
                        <td className="px-4 py-2 font-mono text-neutral-900">{serial.serial_number}</td>
                        <td className="px-4 py-2 text-neutral-700">{serial.batch_id || '—'}</td>
                        <td className="px-4 py-2">
                          <span
                            className={`px-2 py-1 rounded text-xs font-medium capitalize ${
                              serial.unit_condition === 'new'
                                ? 'bg-green-100 text-green-800'
                                : serial.unit_condition === 'used'
                                  ? 'bg-blue-100 text-blue-800'
                                  : serial.unit_condition === 'damaged'
                                    ? 'bg-red-100 text-red-800'
                                    : 'bg-yellow-100 text-yellow-800'
                            }`}
                          >
                            {serial.unit_condition}
                          </span>
                        </td>
                        <td className="px-4 py-2 text-neutral-700">
                          {serial.assigned_to_order_id ? `Order #${serial.assigned_to_order_id}` : '—'}
                        </td>
                        <td className="px-4 py-2 text-neutral-600">{formatDate(serial.created_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  );
};

export default InventoryDetailPage;
