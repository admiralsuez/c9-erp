import React, { useEffect, useState } from 'react';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { X, Plus, Edit2, Trash2, Loader, AlertCircle, Download, Upload } from 'lucide-react';
import {
  useSettings,
  useUpdateSettings,
  useUsers,
  useCreateUser,
  useUpdateUser,
  useDeleteUser,
  useRoles,
  usePermissions,
  useCreateRole,
  useUpdateRole,
  useWarehouses,
  useCreateWarehouse,
  useCreateZone,
  useCreateRack,
  useCreateShelf,
  useCreateBin,
  useCategories,
  useCreateCategory,
  useUpdateCategory,
  useDeleteCategory,
  useAuditLogs,
  useSignature,
  useUpsertSignature,
  useDownloadBackup,
  useUploadBackup,
  useListBackups,
} from '../../hooks/useSettings';
import { useAuth } from '../../hooks/useAuth';
import { SignatureCapture } from '../../components/SignatureCapture';
import { formatDateTime } from '../../utils/format';

const ErrorMessage: React.FC<{ message: string }> = ({ message }) => (
  <div className="p-3 bg-error/10 border border-error/30 rounded-lg text-sm text-error flex items-center gap-2">
    <AlertCircle className="w-4 h-4" />
    {message}
  </div>
);

// ============ COMPANY PROFILE SECTION ============
export const CompanyProfileSection: React.FC = () => {
  const { data: settings, isLoading, error } = useSettings();
  const updateSettings = useUpdateSettings();
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    company_name: '',
    company_gst: '',
    company_contact: '',
    company_address: '',
    company_logo_url: '',
    order_number_format: '',
    requisition_number_format: '',
    default_low_stock_threshold: 0,
  });

  useEffect(() => {
    if (settings) {
      setFormData({
        company_name: settings.company_name || '',
        company_gst: settings.company_gst || '',
        company_contact: settings.company_contact || '',
        company_address: settings.company_address || '',
        company_logo_url: settings.company_logo_url || '',
        order_number_format: settings.order_number_format || '',
        requisition_number_format: settings.requisition_number_format || '',
        default_low_stock_threshold: settings.default_low_stock_threshold || 0,
      });
    }
  }, [settings]);

  const handleSave = () => {
    updateSettings.mutate(formData, {
      onSuccess: () => setIsEditing(false),
    });
  };

  if (isLoading) return <Card padding="lg"><Loader className="w-5 h-5 animate-spin" /></Card>;
  if (error) return <Card padding="lg"><ErrorMessage message="Could not load company settings." /></Card>;

  if (isEditing) {
    return (
      <Card padding="lg">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-neutral-900">Edit Company Profile</h2>
          <button onClick={() => setIsEditing(false)} className="p-1 hover:bg-neutral-100 rounded">
            <X className="w-5 h-5 text-neutral-600" />
          </button>
        </div>
        <div className="space-y-4">
          {[
            ['company_name', 'Company Name'],
            ['company_gst', 'GST Number'],
            ['company_contact', 'Contact'],
            ['company_logo_url', 'Company Logo URL'],
            ['order_number_format', 'Order Number Format'],
            ['requisition_number_format', 'Requisition Number Format'],
          ].map(([key, label]) => (
            <div key={key}>
              <label className="block text-sm font-medium mb-2 text-neutral-700">{label}</label>
              <input
                type="text"
                value={(formData as any)[key]}
                onChange={(e) => setFormData({ ...formData, [key]: e.target.value })}
                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                disabled={updateSettings.isPending}
              />
            </div>
          ))}
          <div>
            <label className="block text-sm font-medium mb-2 text-neutral-700">Default Low Stock Threshold</label>
            <input
              type="number"
              value={formData.default_low_stock_threshold}
              onChange={(e) => setFormData({ ...formData, default_low_stock_threshold: Number(e.target.value) })}
              className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              disabled={updateSettings.isPending}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2 text-neutral-700">Address</label>
            <textarea
              value={formData.company_address}
              onChange={(e) => setFormData({ ...formData, company_address: e.target.value })}
              rows={3}
              className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              disabled={updateSettings.isPending}
            />
          </div>
          {updateSettings.error && <ErrorMessage message="Could not save settings." />}
          <div className="flex gap-2 justify-end">
            <Button onClick={() => setIsEditing(false)} disabled={updateSettings.isPending} className="px-4 py-2 border border-neutral-300 text-neutral-700 hover:bg-neutral-50">Cancel</Button>
            <Button onClick={handleSave} disabled={updateSettings.isPending} className="px-4 py-2 bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50 flex items-center gap-2">
              {updateSettings.isPending && <Loader className="w-4 h-4 animate-spin" />}
              {updateSettings.isPending ? 'Saving...' : 'Save'}
            </Button>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card padding="lg">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-neutral-900">Company Profile</h2>
        <Button onClick={() => setIsEditing(true)} className="flex items-center gap-2 text-sm bg-primary-600 text-white hover:bg-primary-700">
          <Edit2 className="w-4 h-4" />
          Edit
        </Button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div><p className="text-sm text-neutral-600 font-medium mb-1">Company Name</p><p className="text-neutral-900">{settings?.company_name || '—'}</p></div>
        <div><p className="text-sm text-neutral-600 font-medium mb-1">GST</p><p className="text-neutral-900">{settings?.company_gst || '—'}</p></div>
        <div><p className="text-sm text-neutral-600 font-medium mb-1">Contact</p><p className="text-neutral-900">{settings?.company_contact || '—'}</p></div>
        <div><p className="text-sm text-neutral-600 font-medium mb-1">Low Stock Threshold</p><p className="text-neutral-900">{settings?.default_low_stock_threshold}</p></div>
        <div className="md:col-span-2"><p className="text-sm text-neutral-600 font-medium mb-1">Address</p><p className="text-neutral-900">{settings?.company_address || '—'}</p></div>
      </div>
    </Card>
  );
};

// ============ USERS & PERMISSIONS SECTION ============
export const UsersSection: React.FC = () => {
  const { data, isLoading, error } = useUsers(1, 100);
  const { data: roles = [] } = useRoles();
  const { data: permissions = [] } = usePermissions();
  const createUser = useCreateUser();
  const updateUser = useUpdateUser();
  const deleteUser = useDeleteUser();
  const createRole = useCreateRole();
  const updateRole = useUpdateRole();
  const [isAdding, setIsAdding] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState({ full_name: '', email: '', password: '', department: '', role_id: 0 });
  const [isAddingRole, setIsAddingRole] = useState(false);
  const [editingRoleId, setEditingRoleId] = useState<number | null>(null);
  const [roleForm, setRoleForm] = useState({ name: '', description: '', permission_ids: [] as number[] });

  const selectedRole = roles.find((r) => r.id === form.role_id);

  useEffect(() => {
    if (!form.role_id && roles[0]) setForm((prev) => ({ ...prev, role_id: roles[0].id }));
  }, [roles, form.role_id]);

  const reset = () => {
    setForm({ full_name: '', email: '', password: '', department: '', role_id: roles[0]?.id || 0 });
    setIsAdding(false);
    setEditingId(null);
  };

  const submit = () => {
    if (!form.full_name || !form.email || !form.role_id) return;
    if (editingId) {
      updateUser.mutate({ userId: editingId, data: { full_name: form.full_name, email: form.email, department: form.department, role_id: form.role_id } }, { onSuccess: reset });
    } else {
      if (!form.password) return;
      createUser.mutate(form, { onSuccess: reset });
    }
  };

  const resetRoleForm = () => {
    setRoleForm({ name: '', description: '', permission_ids: [] });
    setIsAddingRole(false);
    setEditingRoleId(null);
  };

  const submitRole = () => {
    if (!roleForm.name.trim()) return;
    if (editingRoleId) {
      updateRole.mutate(
        { roleId: editingRoleId, data: { name: roleForm.name, description: roleForm.description || undefined, permission_ids: roleForm.permission_ids } },
        { onSuccess: resetRoleForm }
      );
    } else {
      createRole.mutate(
        { name: roleForm.name, description: roleForm.description || undefined, permission_ids: roleForm.permission_ids },
        { onSuccess: resetRoleForm }
      );
    }
  };

  const togglePermission = (permId: number) => {
    setRoleForm((prev) => ({
      ...prev,
      permission_ids: prev.permission_ids.includes(permId)
        ? prev.permission_ids.filter((id) => id !== permId)
        : [...prev.permission_ids, permId],
    }));
  };

  return (
    <Card padding="lg">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-neutral-900">Users & Permissions</h2>
        <div className="flex gap-2">
          <Button onClick={() => setIsAddingRole(!isAddingRole)} className="flex items-center gap-2 text-sm bg-info text-white hover:bg-info/90">
            <Plus className="w-4 h-4" />
            Add Role
          </Button>
          <Button onClick={() => setIsAdding(!isAdding)} className="flex items-center gap-2 text-sm bg-primary-600 text-white hover:bg-primary-700">
            <Plus className="w-4 h-4" />
            Add User
          </Button>
        </div>
      </div>

      {/* Role Add/Edit Form */}
      {(isAddingRole || editingRoleId) && (
        <div className="mb-6 p-4 bg-neutral-50 rounded-lg border border-neutral-200 space-y-3">
          <h3 className="text-sm font-semibold text-neutral-900">{editingRoleId ? 'Edit Role' : 'Add New Role'}</h3>
          <input type="text" placeholder="Role name" value={roleForm.name} onChange={(e) => setRoleForm({ ...roleForm, name: e.target.value })} className="w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm" />
          <input type="text" placeholder="Description (optional)" value={roleForm.description} onChange={(e) => setRoleForm({ ...roleForm, description: e.target.value })} className="w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm" />
          <div>
            <p className="text-sm font-medium text-neutral-700 mb-2">Permissions:</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {permissions.map((perm) => (
                <label key={perm.id} className="flex items-center gap-2 text-sm cursor-pointer">
                  <input
                    type="checkbox"
                    checked={roleForm.permission_ids.includes(perm.id)}
                    onChange={() => togglePermission(perm.id)}
                    className="w-4 h-4 text-primary-600 rounded"
                  />
                  <span className="text-neutral-700">{perm.description || perm.code}</span>
                </label>
              ))}
            </div>
          </div>
          {(createRole.error || updateRole.error) && <ErrorMessage message="Could not save role." />}
          <div className="flex gap-2">
            <Button onClick={submitRole} disabled={!roleForm.name.trim() || createRole.isPending || updateRole.isPending} className="px-3 py-2 bg-primary-600 text-white hover:bg-primary-700 text-sm disabled:opacity-50">
              {editingRoleId ? 'Save Role' : 'Create Role'}
            </Button>
            <Button onClick={resetRoleForm} className="px-3 py-2 border border-neutral-300 text-neutral-700 hover:bg-neutral-50 text-sm">Cancel</Button>
          </div>
        </div>
      )}

      {/* User Add/Edit Form */}
      {(isAdding || editingId) && (
        <div className="mb-6 p-4 bg-neutral-50 rounded-lg border border-neutral-200 space-y-3">
          <input type="text" placeholder="Full name" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} className="w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm" />
          <input type="email" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm" />
          {!editingId && <input type="password" placeholder="Temporary password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} className="w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm" />}
          <input type="text" placeholder="Department" value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })} className="w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm" />
          <select value={form.role_id} onChange={(e) => setForm({ ...form, role_id: Number(e.target.value) })} className="w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm">
            {roles.map((role) => <option key={role.id} value={role.id}>{role.name}</option>)}
          </select>
          {selectedRole && selectedRole.permissions.length > 0 && (
            <div className="p-3 bg-white rounded border border-neutral-200">
              <p className="text-xs font-semibold text-neutral-700 mb-2">Permissions granted by "{selectedRole.name}":</p>
              <div className="flex flex-wrap gap-2">
                {selectedRole.permissions.map((p) => (
                  <span key={p.id} className="text-xs px-2 py-1 bg-primary-50 text-primary-700 rounded-full border border-primary-200">
                    {p.description || p.code}
                  </span>
                ))}
              </div>
            </div>
          )}
          {(createUser.error || updateUser.error) && <ErrorMessage message="Could not save user." />}
          <div className="flex gap-2">
            <Button onClick={submit} disabled={createUser.isPending || updateUser.isPending} className="px-3 py-2 bg-primary-600 text-white hover:bg-primary-700 text-sm disabled:opacity-50">{editingId ? 'Save' : 'Add'}</Button>
            <Button onClick={reset} className="px-3 py-2 border border-neutral-300 text-neutral-700 hover:bg-neutral-50 text-sm">Cancel</Button>
          </div>
        </div>
      )}
      {isLoading && <Loader className="w-5 h-5 animate-spin" />}
      {error && <ErrorMessage message="Could not load users. Admin access may be required." />}
      <div className="space-y-2">
        {data?.items.map((user) => (
          <div key={user.id} className="flex items-center justify-between p-3 bg-neutral-50 rounded-lg">
            <div className="flex-1 min-w-0">
              <p className="font-medium text-neutral-900 truncate">{user.full_name}</p>
              <p className="text-xs text-neutral-600 truncate">{user.email}{user.department ? ` • ${user.department}` : ''}</p>
            </div>
            <div className="flex items-center gap-3 ml-3 flex-shrink-0">
              <span className="text-xs font-semibold px-2 py-1 bg-primary-100 text-primary-700 rounded whitespace-nowrap">{user.role?.name || 'Role'}</span>
              <button onClick={() => { setEditingId(user.id); setIsAdding(false); setForm({ full_name: user.full_name, email: user.email, password: '', department: user.department || '', role_id: user.role?.id || roles[0]?.id || 0 }); }} className="p-1 text-primary-600 hover:bg-primary-50 rounded"><Edit2 className="w-4 h-4" /></button>
              <button onClick={() => { if (window.confirm('Are you sure you want to delete this user?')) deleteUser.mutate(user.id); }} className="p-1 text-error hover:bg-error/10 rounded"><Trash2 className="w-4 h-4" /></button>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
};

// ============ WAREHOUSE STRUCTURE SECTION ============
export const WarehouseSection: React.FC = () => {
  const { data, isLoading, error } = useWarehouses(1, 100);
  const createWarehouse = useCreateWarehouse();
  const createZone = useCreateZone();
  const createRack = useCreateRack();
  const createShelf = useCreateShelf();
  const createBin = useCreateBin();
  const [type, setType] = useState('warehouse');
  const [name, setName] = useState('');
  const [address, setAddress] = useState('');
  const [warehouseId, setWarehouseId] = useState(0);
  const [zoneId, setZoneId] = useState(0);
  const [rackId, setRackId] = useState(0);
  const [shelfId, setShelfId] = useState(0);

  const warehouses = data?.items || [];
  const selectedWarehouse = warehouses.find((w) => w.id === warehouseId);
  const selectedZone = selectedWarehouse?.zones.find((z) => z.id === zoneId);
  const selectedRack = selectedZone?.racks.find((r) => r.id === rackId);

  const addLocation = () => {
    if (!name.trim()) return;
    if (type === 'warehouse') createWarehouse.mutate({ name, address }, { onSuccess: () => { setName(''); setAddress(''); } });
    if (type === 'zone' && warehouseId) createZone.mutate({ warehouseId, data: { name } }, { onSuccess: () => setName('') });
    if (type === 'rack' && warehouseId && zoneId) createRack.mutate({ warehouseId, zoneId, data: { name } }, { onSuccess: () => setName('') });
    if (type === 'shelf' && warehouseId && zoneId && rackId) createShelf.mutate({ warehouseId, zoneId, rackId, data: { name } }, { onSuccess: () => setName('') });
    if (type === 'bin' && warehouseId && zoneId && rackId && shelfId) createBin.mutate({ warehouseId, zoneId, rackId, shelfId, data: { name } }, { onSuccess: () => setName('') });
  };

  return (
    <Card padding="lg">
      <h2 className="text-lg font-semibold text-neutral-900 mb-4">Warehouse Structure</h2>
      <div className="mb-6 p-4 bg-neutral-50 rounded-lg border border-neutral-200 space-y-3">
        <select value={type} onChange={(e) => setType(e.target.value)} className="w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm">
          <option value="warehouse">Warehouse</option><option value="zone">Zone</option><option value="rack">Rack</option><option value="shelf">Shelf</option><option value="bin">Bin</option>
        </select>
        {type !== 'warehouse' && <select value={warehouseId} onChange={(e) => setWarehouseId(Number(e.target.value))} className="w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm"><option value={0}>Select warehouse</option>{warehouses.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}</select>}
        {['rack', 'shelf', 'bin'].includes(type) && selectedWarehouse && <select value={zoneId} onChange={(e) => setZoneId(Number(e.target.value))} className="w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm"><option value={0}>Select zone</option>{selectedWarehouse.zones.map((z) => <option key={z.id} value={z.id}>{z.name}</option>)}</select>}
        {['shelf', 'bin'].includes(type) && selectedZone && <select value={rackId} onChange={(e) => setRackId(Number(e.target.value))} className="w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm"><option value={0}>Select rack</option>{selectedZone.racks.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}</select>}
        {type === 'bin' && selectedRack && <select value={shelfId} onChange={(e) => setShelfId(Number(e.target.value))} className="w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm"><option value={0}>Select shelf</option>{selectedRack.shelves.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}</select>}
        <input type="text" placeholder={`${type} name`} value={name} onChange={(e) => setName(e.target.value)} className="w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm" />
        {type === 'warehouse' && <input type="text" placeholder="Address" value={address} onChange={(e) => setAddress(e.target.value)} className="w-full px-3 py-2 border border-neutral-300 rounded-lg text-sm" />}
        <Button onClick={addLocation} className="px-3 py-2 bg-primary-600 text-white hover:bg-primary-700 text-sm flex items-center gap-2"><Plus className="w-4 h-4" />Add</Button>
      </div>
      {isLoading && <Loader className="w-5 h-5 animate-spin" />}
      {error && <ErrorMessage message="Could not load warehouses." />}
      <div className="space-y-3">
        {warehouses.map((warehouse) => (
          <div key={warehouse.id} className="p-3 bg-neutral-50 rounded-lg border border-neutral-100">
            <p className="font-semibold text-neutral-900">{warehouse.name}</p>
            <p className="text-xs text-neutral-600 mb-2">{warehouse.address || 'No address'}</p>
            {warehouse.zones.map((zone) => (
              <div key={zone.id} className="ml-4 mt-2 text-sm">
                <p className="font-medium text-neutral-800">Zone: {zone.name}</p>
                {zone.racks.map((rack) => <p key={rack.id} className="ml-4 text-neutral-600">Rack: {rack.name} • {rack.shelves.length} shelves</p>)}
              </div>
            ))}
          </div>
        ))}
      </div>
    </Card>
  );
};

// ============ ITEM CATEGORIES SECTION ============
export const CategoriesSection: React.FC = () => {
  const { data: categories = [], isLoading, error } = useCategories();
  const createCategory = useCreateCategory();
  const updateCategory = useUpdateCategory();
  const deleteCategory = useDeleteCategory();
  const [newCategory, setNewCategory] = useState('');
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editName, setEditName] = useState('');

  const addCategory = () => {
    if (!newCategory.trim()) return;
    createCategory.mutate({ name: newCategory.trim() }, { onSuccess: () => setNewCategory('') });
  };

  const startEdit = (cat: { id: number; name: string }) => {
    setEditingId(cat.id);
    setEditName(cat.name);
  };

  const saveEdit = () => {
    if (!editName.trim() || editingId === null) return;
    updateCategory.mutate(
      { categoryId: editingId, data: { name: editName.trim() } },
      { onSuccess: () => setEditingId(null) }
    );
  };

  const confirmDelete = (catId: number) => {
    if (window.confirm('Delete this category? Items in this category will become uncategorized.')) {
      deleteCategory.mutate(catId);
    }
  };

  return (
    <Card padding="lg">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-neutral-900">Item Categories</h2>
      </div>
      <div className="mb-6 p-4 bg-neutral-50 rounded-lg border border-neutral-200 flex gap-2">
        <input type="text" placeholder="Category Name" value={newCategory} onChange={(e) => setNewCategory(e.target.value)} className="flex-1 px-3 py-2 border border-neutral-300 rounded-lg text-sm" />
        <Button onClick={addCategory} disabled={!newCategory.trim() || createCategory.isPending} className="px-3 py-2 bg-primary-600 text-white hover:bg-primary-700 text-sm disabled:opacity-50">Add</Button>
      </div>
      {isLoading && <Loader className="w-5 h-5 animate-spin" />}
      {error && <ErrorMessage message="Could not load categories." />}
      {(createCategory.error || updateCategory.error || deleteCategory.error) && <ErrorMessage message="Could not perform category operation." />}
      <div className="space-y-2">
        {categories.map((cat) => (
          <div key={cat.id} className="flex items-center justify-between p-3 bg-neutral-50 rounded-lg border border-neutral-100">
            {editingId === cat.id ? (
              <div className="flex-1 flex gap-2 items-center">
                <input
                  type="text"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className="flex-1 px-3 py-2 border border-neutral-300 rounded-lg text-sm"
                  autoFocus
                />
                <Button onClick={saveEdit} disabled={!editName.trim() || updateCategory.isPending} className="px-3 py-1 bg-primary-600 text-white text-xs">Save</Button>
                <Button onClick={() => setEditingId(null)} className="px-3 py-1 border border-neutral-300 text-neutral-700 text-xs">Cancel</Button>
              </div>
            ) : (
              <>
                <div>
                  <p className="font-medium text-neutral-900">{cat.name}</p>
                  <p className="text-xs text-neutral-600">{cat.parent_id ? `Parent #${cat.parent_id}` : 'Root category'}</p>
                </div>
                <div className="flex items-center gap-2">
                  <button onClick={() => startEdit(cat)} className="p-1 text-primary-600 hover:bg-primary-50 rounded"><Edit2 className="w-4 h-4" /></button>
                  <button onClick={() => confirmDelete(cat.id)} className="p-1 text-error hover:bg-error/10 rounded"><Trash2 className="w-4 h-4" /></button>
                </div>
              </>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
};

// ============ APPROVAL MATRIX SECTION ============
export const ApprovalMatrixSection: React.FC = () => (
  <Card padding="lg">
    <h2 className="text-lg font-semibold text-neutral-900 mb-4">Approval Matrix</h2>
    <p className="text-sm text-neutral-600">Approval rules are managed by backend approval-rule configuration and are not hardcoded here.</p>
  </Card>
);

// ============ AUDIT LOG SECTION ============
export const AuditLogSection: React.FC = () => {
  const [filters, setFilters] = useState({ action: '', entity_type: '' });
  const [debouncedFilters, setDebouncedFilters] = useState(filters);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedFilters(filters), 300);
    return () => clearTimeout(timer);
  }, [filters]);

  const { data, isLoading, error } = useAuditLogs(1, 50, {
    action: debouncedFilters.action || undefined,
    entity_type: debouncedFilters.entity_type || undefined,
  });

  return (
    <Card padding="lg">
      <h2 className="text-lg font-semibold text-neutral-900 mb-4">Audit Log</h2>
      <div className="mb-4 grid grid-cols-1 md:grid-cols-2 gap-3">
        <input
          type="text"
          placeholder="Filter by action"
          value={filters.action}
          onChange={(e) => setFilters({ ...filters, action: e.target.value })}
          className="px-3 py-2 border border-neutral-300 rounded-lg text-sm"
        />
        <input
          type="text"
          placeholder="Filter by entity type"
          value={filters.entity_type}
          onChange={(e) => setFilters({ ...filters, entity_type: e.target.value })}
          className="px-3 py-2 border border-neutral-300 rounded-lg text-sm"
        />
      </div>
      {isLoading && <Loader className="w-5 h-5 animate-spin" />}
      {error && <ErrorMessage message="Could not load audit logs. Admin access may be required." />}
      <div className="space-y-2">
        {data?.items.map((log) => (
          <div key={log.id} className="p-3 bg-neutral-50 rounded-lg border border-neutral-100">
            <div className="flex items-center justify-between mb-1">
              <p className="font-medium text-neutral-900">{log.action || 'Unknown action'}</p>
              <span className="text-xs text-neutral-500">{log.created_at ? formatDateTime(log.created_at) : '—'}</span>
            </div>
            <p className="text-sm text-neutral-600">
              User #{log.user_id} changed {log.entity_type || 'unknown'} #{log.entity_id || 'N/A'}
            </p>
          </div>
        ))}
        {!isLoading && !data?.items?.length && <p className="text-sm text-neutral-500">No audit logs found.</p>}
      </div>
    </Card>
  );
};

// ============ NOTIFICATIONS SECTION ============
export const NotificationsSection: React.FC = () => (
  <Card padding="lg">
    <h2 className="text-lg font-semibold text-neutral-900 mb-4">Notification Preferences</h2>
    <p className="text-sm text-neutral-600">No notification preferences API exists yet. Low-stock and order email notifications are handled by backend services.</p>
  </Card>
);

// ============ USER PROFILE & SIGNATURE SECTION ============
export const UserProfileSection: React.FC = () => {
  const { user: currentUser } = useAuth();
  const userId = currentUser?.id ?? null;
  const { data: existingSignature, isLoading: sigLoading } = useSignature(userId);
  const upsertSignature = useUpsertSignature();
  const [signature, setSignature] = React.useState<string | null>(null);
  const [saveMessage, setSaveMessage] = React.useState('');

  React.useEffect(() => {
    if (existingSignature?.signature_data) {
      setSignature(existingSignature.signature_data);
    }
  }, [existingSignature]);

  const handleSignatureCapture = (signatureData: string) => {
    if (!userId) return;
    setSignature(signatureData);
    setSaveMessage('');
    upsertSignature.mutate(
      { userId, data: { signature_data: signatureData } },
      {
        onSuccess: () => {
          setSaveMessage('✓ Signature saved successfully! You can now use it for faster order approvals.');
          setTimeout(() => setSaveMessage(''), 4000);
        },
        onError: () => {
          setSaveMessage('✗ Failed to save signature. Please try again.');
        },
      }
    );
  };

  return (
    <Card padding="lg">
      <h2 className="text-lg font-semibold text-neutral-900 mb-4">User Profile & Digital Signature</h2>
      <p className="text-sm text-neutral-600 mb-6">
        Upload or draw your digital signature below. This will be used to sign off on order approvals, reducing manual signature collection on delivery documents.
      </p>
      
      {saveMessage && (
        <div className={`mb-4 p-3 rounded-lg text-sm ${
          saveMessage.startsWith('✓')
            ? 'bg-success/10 border border-success/30 text-success'
            : 'bg-error/10 border border-error/30 text-error'
        }`}>
          {saveMessage}
        </div>
      )}

      {sigLoading ? (
        <div className="flex items-center gap-2 text-neutral-500 py-4">
          <Loader className="w-4 h-4 animate-spin" />
          <span>Loading signature...</span>
        </div>
      ) : (
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-neutral-900">Digital Signature</h3>
          <SignatureCapture
            onCapture={handleSignatureCapture}
            existingSignature={signature || undefined}
            disabled={upsertSignature.isPending}
          />
          {upsertSignature.isPending && (
            <div className="flex items-center gap-2 text-sm text-primary-600">
              <Loader className="w-4 h-4 animate-spin" />
              Saving signature...
            </div>
          )}
        </div>
      )}

      <div className="mt-6 p-4 bg-info/10 rounded-lg">
        <h3 className="text-sm font-semibold text-info mb-2">ℹ️ How it works:</h3>
        <ul className="text-sm text-info space-y-1 ml-4">
          <li>• Draw or upload your signature</li>
          <li>• Your signature will appear on order approval documents</li>
          <li>• Receiver can compare with physical signature on delivery challan</li>
          <li>• Provides audit trail and faster approval workflow</li>
        </ul>
      </div>
    </Card>
  );
};

// ============ BACKUP & RESTORE SECTION ============
export const BackupSection: React.FC = () => {
  const downloadBackup = useDownloadBackup();
  const uploadBackup = useUploadBackup();
  const { data: backups = [] } = useListBackups();
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      uploadBackup.mutate(file);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  return (
    <Card padding="lg">
      <h2 className="text-lg font-semibold text-neutral-900 mb-4">Backup & Restore</h2>
      <p className="text-sm text-neutral-600 mb-6">Download backups of your database or restore from a previous backup. A safety backup is automatically created before any restoration.</p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {/* Download Backup */}
        <div className="p-4 border border-neutral-200 rounded-lg">
          <h3 className="text-sm font-semibold text-neutral-900 mb-3">Download Backup</h3>
          <p className="text-xs text-neutral-600 mb-4">Create and download a complete database backup file for safekeeping.</p>
          <button
            onClick={() => downloadBackup.mutate()}
            disabled={downloadBackup.isPending}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors text-sm"
          >
            {downloadBackup.isPending ? (
              <>
                <Loader className="w-4 h-4 animate-spin" />
                Creating...
              </>
            ) : (
              <>
                <Download className="w-4 h-4" />
                Download Now
              </>
            )}
          </button>
        </div>

        {/* Restore Backup */}
        <div className="p-4 border border-neutral-200 rounded-lg">
          <h3 className="text-sm font-semibold text-neutral-900 mb-3">Restore from Backup</h3>
          <p className="text-xs text-neutral-600 mb-4">Select a backup file to restore. Current data will be preserved as a safety backup.</p>
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileSelect}
            accept=".db,.sql"
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploadBackup.isPending}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 border border-primary-300 text-primary-700 rounded-lg hover:bg-primary-50 disabled:opacity-50 transition-colors text-sm"
          >
            {uploadBackup.isPending ? (
              <>
                <Loader className="w-4 h-4 animate-spin" />
                Restoring...
              </>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                Select File
              </>
            )}
          </button>
        </div>
      </div>

      {/* Safety warning */}
      <div className="p-4 bg-warning/10 border border-warning/30 rounded-lg mb-6">
        <p className="text-sm text-warning font-medium mb-2">⚠️ Important:</p>
        <ul className="text-xs text-warning space-y-1 ml-4">
          <li>• Always keep regular backups in a safe location</li>
          <li>• Restoring a backup will replace all current data</li>
          <li>• A safety backup is created before restoration</li>
          <li>• This action requires admin permissions</li>
        </ul>
      </div>

      {/* Available backups */}
      {Array.isArray(backups) && backups.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-neutral-900 mb-3">Available Backups</h3>
          <div className="space-y-2">
            {backups.map((backup: any, idx: number) => (
              <div key={idx} className="p-3 bg-neutral-50 rounded-lg border border-neutral-100">
                <p className="text-sm font-medium text-neutral-900">{backup.filename || backup}</p>
                <p className="text-xs text-neutral-600 mt-1">{backup.created_at || 'Date unavailable'}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
};
