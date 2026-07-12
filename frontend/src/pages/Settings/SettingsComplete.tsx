import React, { useState } from 'react';
import { Card } from '../../components/ui/Card';
import {
  Building2,
  Users,
  Warehouse,
  Tag,
  CheckCircle,
  FileText,
  Bell,
  ChevronRight,
  ArrowLeft,
  Loader,
  HardDrive,
} from 'lucide-react';
import {
  CompanyProfileSection,
  UsersSection,
  WarehouseSection,
  CategoriesSection,
  ApprovalMatrixSection,
  AuditLogSection,
  NotificationsSection,
  UserProfileSection,
  BackupSection,
} from './Editable';
import { useSystemInfo } from '../../hooks/useSettings';

interface SettingsSection {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  color: string;
}

const settingsSections: SettingsSection[] = [
  {
    id: 'company',
    title: 'Company Profile',
    description: 'Manage company information, contact details, and branding',
    icon: <Building2 className="w-6 h-6" />,
    color: 'bg-primary-50 text-primary-600',
  },
  {
    id: 'users',
    title: 'Users & Permissions',
    description: 'Manage team members, roles, and access permissions',
    icon: <Users className="w-6 h-6" />,
    color: 'bg-primary-100 text-primary-700',
  },
  {
    id: 'warehouse',
    title: 'Warehouse Structure',
    description: 'Configure warehouse zones, shelves, and locations',
    icon: <Warehouse className="w-6 h-6" />,
    color: 'bg-warning/10 text-warning',
  },
  {
    id: 'categories',
    title: 'Item Categories',
    description: 'Create and manage inventory item categories',
    icon: <Tag className="w-6 h-6" />,
    color: 'bg-success/10 text-success',
  },
  {
    id: 'approvals',
    title: 'Approval Matrix',
    description: 'Set up approval workflows and authorization levels',
    icon: <CheckCircle className="w-6 h-6" />,
    color: 'bg-error/10 text-error',
  },
  {
    id: 'audit',
    title: 'Audit Log',
    description: 'View system activity, changes, and user actions',
    icon: <FileText className="w-6 h-6" />,
    color: 'bg-warning/20 text-warning',
  },
  {
    id: 'notifications',
    title: 'Notifications',
    description: 'Configure alert settings and notification preferences',
    icon: <Bell className="w-6 h-6" />,
    color: 'bg-info/10 text-info',
  },
  {
    id: 'signature',
    title: 'Digital Signature',
    description: 'Manage your digital signature for order approvals',
    icon: <FileText className="w-6 h-6" />,
    color: 'bg-primary-50 text-primary-600',
  },
  {
    id: 'backup',
    title: 'Backup & Restore',
    description: 'Download database backups and restore from previous backups',
    icon: <HardDrive className="w-6 h-6" />,
    color: 'bg-error/10 text-error',
  },
];

export const SettingsPageComplete: React.FC = () => {
  const [selectedSection, setSelectedSection] = useState<string | null>(null);
  const selectedSectionData = settingsSections.find((s) => s.id === selectedSection);

  if (selectedSection) {
    return (
      <div className="space-y-6 pb-6">
        {/* Header with Back Button */}
        <div className="flex items-center gap-4">
          <button
            onClick={() => setSelectedSection(null)}
            className="p-2 hover:bg-neutral-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-neutral-600" />
          </button>
          <div>
            <h1 className="text-3xl font-bold text-neutral-900">
              {selectedSectionData?.title}
            </h1>
            <p className="text-neutral-600 mt-1">
              {selectedSectionData?.description}
            </p>
          </div>
        </div>

        {/* Section Details */}
        {selectedSection === 'company' && <CompanyProfileSection />}
        {selectedSection === 'users' && <UsersSection />}
        {selectedSection === 'warehouse' && <WarehouseSection />}
        {selectedSection === 'categories' && <CategoriesSection />}
        {selectedSection === 'approvals' && <ApprovalMatrixSection />}
        {selectedSection === 'audit' && <AuditLogSection />}
        {selectedSection === 'notifications' && <NotificationsSection />}
        {selectedSection === 'signature' && <UserProfileSection />}
        {selectedSection === 'backup' && <BackupSection />}
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-neutral-900">Settings</h1>
        <p className="text-neutral-600 mt-1">
          Manage your system configuration, users, and preferences
        </p>
      </div>

      {/* Settings Overview Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {settingsSections.map((section) => (
          <Card
            key={section.id}
            padding="lg"
            className="cursor-pointer hover:shadow-md transition-all"
            onClick={() => setSelectedSection(section.id)}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-4 flex-grow">
                <div
                  className={`w-12 h-12 rounded-lg flex items-center justify-center flex-shrink-0 ${section.color}`}
                >
                  {section.icon}
                </div>
                <div className="min-w-0">
                  <h3 className="text-lg font-semibold text-neutral-900">
                    {section.title}
                  </h3>
                  <p className="text-sm text-neutral-600 mt-1">
                    {section.description}
                  </p>
                </div>
              </div>
              <ChevronRight className="w-5 h-5 text-neutral-400 flex-shrink-0 ml-2" />
            </div>
          </Card>
        ))}
      </div>

      {/* System Information */}
      <SystemInfoCard />
    </div>
  );
};

const SystemInfoCard: React.FC = () => {
  const { data, isLoading, error } = useSystemInfo();

  return (
    <Card padding="lg">
      <h2 className="text-lg font-semibold text-neutral-900 mb-4">
        System Information
      </h2>
      {isLoading && (
        <div className="flex items-center gap-2 text-neutral-500 py-2">
          <Loader className="w-4 h-4 animate-spin" />
          <span>Loading...</span>
        </div>
      )}
      {error && (
        <p className="text-sm text-error">Could not load system information.</p>
      )}
      {data && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <p className="text-sm text-neutral-600 font-medium mb-1">
              System Version
            </p>
            <p className="text-neutral-900 font-mono">v{data.system_version}</p>
          </div>
          <div>
            <p className="text-sm text-neutral-600 font-medium mb-1">
              Last Updated
            </p>
            <p className="text-neutral-900">
              {data.last_updated
                ? (() => { const d = new Date(data.last_updated); return `${d.getFullYear()} ${d.toLocaleDateString('en-US', { month: 'long' })} ${d.getDate()}`; })()
                : '—'}
            </p>
          </div>
          <div>
            <p className="text-sm text-neutral-600 font-medium mb-1">
              Database Size
            </p>
            <p className="text-neutral-900">
              {data.database_size_mb > 0
                ? `${data.database_size_mb.toFixed(2)} MB`
                : '—'}
            </p>
          </div>
          <div>
            <p className="text-sm text-neutral-600 font-medium mb-1">
              Active Users (30d)
            </p>
            <p className="text-neutral-900">{data.active_users_30d}</p>
          </div>
          <div>
            <p className="text-sm text-neutral-600 font-medium mb-1">
              Total Users
            </p>
            <p className="text-neutral-900">{data.total_users}</p>
          </div>
          <div>
            <p className="text-sm text-neutral-600 font-medium mb-1">
              Total Items / Orders
            </p>
            <p className="text-neutral-900">
              {data.total_items} / {data.total_orders}
            </p>
          </div>
        </div>
      )}
    </Card>
  );
};

export default SettingsPageComplete;
