import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useNavigate, useLocation } from 'react-router-dom';
import { useUnreadCount } from '../hooks/useNotifications';
import {
  LayoutDashboard,
  Package,
  Users,
  ShoppingCart,
  Settings,
  LogOut,
  Menu,
  X,
  Search,
  Bell,
  ClipboardCheck,
  BarChart3,
  Plus,
} from 'lucide-react';

interface NavItem {
  label: string;
  icon: React.ReactNode;
  href: string;
  requiredPermission?: string;
}

const navItems: NavItem[] = [
  { label: 'Dashboard', icon: <LayoutDashboard className="w-5 h-5" />, href: '/' },
  { label: 'Inventory', icon: <Package className="w-5 h-5" />, href: '/inventory' },
  { label: 'Vendors', icon: <Users className="w-5 h-5" />, href: '/vendors' },
  { label: 'Orders', icon: <ShoppingCart className="w-5 h-5" />, href: '/orders' },
  { label: 'My Approvals', icon: <ClipboardCheck className="w-5 h-5" />, href: '/approvals' },
  { label: 'Reports', icon: <BarChart3 className="w-5 h-5" />, href: '/reports' },
  { label: 'Settings', icon: <Settings className="w-5 h-5" />, href: '/settings' },
];

interface AppShellProps {
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const { data: unreadCount } = useUnreadCount();

  // Mobile view detection handled via responsive classes

  const handleNavClick = (href: string) => {
    navigate(href);
    setSidebarOpen(false);
  };

  return (
    <div className="min-h-screen bg-neutral-50 flex flex-col md:flex-row">
      {/* Skip to content link */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary-600 focus:text-white focus:rounded-lg"
      >
        Skip to main content
      </a>

      {/* Desktop Sidebar */}
      <aside className="hidden md:flex md:w-64 fixed top-0 left-0 h-screen bg-white border-r border-neutral-200 flex-col z-30" aria-label="Sidebar navigation">
        {/* Logo */}
        <div className="p-6 border-b border-neutral-200">
          <h1 className="text-2xl font-bold text-primary-600">Cloud9 ERP</h1>
        </div>

        {/* Navigation */}
        <nav className="flex-grow overflow-y-auto p-4" aria-label="Main navigation">
          <ul className="space-y-2">
            {navItems.map((item) => (
              <li key={item.href}>
                <button
                  onClick={() => handleNavClick(item.href)}
                  className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg transition-colors ${
                    location.pathname === item.href
                      ? 'bg-primary-100 text-primary-700 font-semibold'
                      : 'text-neutral-700 hover:bg-neutral-100'
                  }`}
                >
                  {item.icon}
                  <span>{item.label}</span>
                </button>
              </li>
            ))}
          </ul>
        </nav>

        {/* User Section */}
        <div className="border-t border-neutral-200 p-4">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-full bg-primary-200 flex items-center justify-center text-primary-700 font-semibold">
              {user?.full_name.charAt(0).toUpperCase() || 'U'}
            </div>
            <div className="flex-grow min-w-0">
              <p className="text-sm font-medium text-neutral-900 truncate">{user?.full_name}</p>
              <p className="text-xs text-neutral-500 truncate">{user?.email}</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="w-full flex items-center gap-2 px-4 py-2 text-sm text-neutral-700 hover:bg-neutral-100 rounded-lg transition-colors"
            aria-label="Logout"
          >
            <LogOut className="w-4 h-4" aria-hidden="true" />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="md:ml-64 flex-grow flex flex-col min-w-0">
        {/* Mobile Header */}
        <header className="md:hidden bg-white border-b border-neutral-200 px-4 py-3 flex items-center justify-between">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 hover:bg-neutral-100 rounded-lg"
            aria-label={sidebarOpen ? 'Close menu' : 'Open menu'}
          >
            {sidebarOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>

          <h1 className="text-lg font-bold text-primary-600">Cloud9 ERP</h1>

          <div className="flex items-center gap-2">
            <button onClick={() => navigate('/notifications')} className="p-2 hover:bg-neutral-100 rounded-lg relative" aria-label="Notifications">
              <Bell className="w-5 h-5 text-neutral-600" />
              {unreadCount != null && unreadCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-error text-white text-[10px] font-bold rounded-full flex items-center justify-center">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </button>
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="w-8 h-8 rounded-full bg-primary-200 flex items-center justify-center text-sm font-semibold text-primary-700"
              aria-label="User menu"
              aria-expanded={showUserMenu}
            >
              {user?.full_name.charAt(0).toUpperCase() || 'U'}
            </button>
          </div>
        </header>

        {/* Desktop Header */}
        <header className="sticky top-0 hidden md:flex bg-white border-b border-neutral-200 px-6 py-4 items-center justify-between z-20">
          <div className="w-80 flex items-center gap-3 bg-neutral-50 px-3 py-2 rounded-lg border border-neutral-200">
            <Search className="w-5 h-5 text-neutral-400 flex-shrink-0" aria-hidden="true" />
            <input
              type="text"
              placeholder="Search this page..."
              aria-label="Search this page"
              className="flex-grow bg-transparent text-sm focus:outline-none"
            />
          </div>

          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/orders/new')}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium text-sm"
              aria-label="Create new order"
            >
              <Plus className="w-5 h-5" />
              <span>Create New Order</span>
            </button>
            <button
              onClick={() => navigate('/notifications')}
              className="p-2 hover:bg-neutral-100 rounded-lg relative"
              aria-label="Notifications"
            >
              <Bell className="w-5 h-5 text-neutral-600" />
              {unreadCount != null && unreadCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-error text-white text-[10px] font-bold rounded-full flex items-center justify-center">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </button>
            <div className="relative">
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="w-10 h-10 rounded-full bg-primary-200 flex items-center justify-center text-sm font-semibold text-primary-700 hover:shadow-md transition-shadow"
                aria-label="User menu"
                aria-expanded={showUserMenu}
                aria-haspopup="true"
              >
                {user?.full_name.charAt(0).toUpperCase() || 'U'}
              </button>

              {/* User Dropdown */}
              {showUserMenu && (
                <div className="absolute top-12 right-0 bg-white border border-neutral-200 rounded-lg shadow-lg z-50 min-w-48" role="menu" aria-label="User menu">
                  <div className="p-3 border-b border-neutral-200">
                    <p className="text-sm font-medium text-neutral-900">{user?.full_name}</p>
                    <p className="text-xs text-neutral-500">{user?.email}</p>
                  </div>
                  <button
                    onClick={logout}
                    className="w-full text-left px-4 py-2 text-sm text-neutral-700 hover:bg-neutral-50 flex items-center gap-2 transition-colors"
                    role="menuitem"
                  >
                    <LogOut className="w-4 h-4" aria-hidden="true" />
                    <span>Logout</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Mobile Sidebar */}
        {/* Mobile Sidebar */}
        {sidebarOpen && (
          <nav className="md:hidden bg-white border-b border-neutral-200 p-4" aria-label="Mobile navigation">
            <ul className="space-y-2">
              {navItems.map((item) => (
                <li key={item.href}>
                  <button
                    onClick={() => handleNavClick(item.href)}
                    className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg transition-colors ${
                      location.pathname === item.href
                        ? 'bg-primary-100 text-primary-700 font-semibold'
                        : 'text-neutral-700 hover:bg-neutral-100'
                    }`}
                  >
                    {item.icon}
                    <span>{item.label}</span>
                  </button>
                </li>
              ))}
              <li>
                <button
                  onClick={logout}
                  className="w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-neutral-700 hover:bg-neutral-100 transition-colors"
                >
                  <LogOut className="w-5 h-5" />
                  <span>Logout</span>
                </button>
              </li>
            </ul>
          </nav>
        )}

        {/* Page Content */}
        <main id="main-content" className="flex-grow overflow-y-auto overflow-x-hidden">
          <div className="p-4 md:p-6">{children}</div>
        </main>
      </div>
    </div>
  );
};

export default AppShell;
