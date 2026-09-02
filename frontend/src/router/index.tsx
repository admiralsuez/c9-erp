import React, { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import { AppShell } from '../layouts/AppShell';
import { ProtectedRoute } from '../components/ProtectedRoute';

// ============ Lazy-loaded routes ============
// Each page is split into its own chunk so the initial bundle only pays for
// Login / Forgot / Reset / Dashboard. Admin / Reports / Inventory detail / etc.
// download on demand when the user navigates there.
const LoginPage = lazy(() => import('../pages/Login').then((m) => ({ default: m.LoginPage })));
const DashboardPage = lazy(() => import('../pages/Dashboard').then((m) => ({ default: m.DashboardPage })));
const InventoryListPage = lazy(() => import('../pages/Inventory/List').then((m) => ({ default: m.InventoryListPage })));
const InventoryDetailPage = lazy(() => import('../pages/Inventory/Detail').then((m) => ({ default: m.InventoryDetailPage })));
const InventoryFormPage = lazy(() => import('../pages/Inventory/Form').then((m) => ({ default: m.InventoryFormPage })));
const SettingsPageComplete = lazy(() => import('../pages/Settings/SettingsComplete').then((m) => ({ default: m.SettingsPageComplete })));
const VendorsListPage = lazy(() => import('../pages/Vendors/List').then((m) => ({ default: m.VendorsListPage })));
const VendorDetailPage = lazy(() => import('../pages/Vendors/Detail').then((m) => ({ default: m.VendorDetailPage })));
const VendorFormPage = lazy(() => import('../pages/Vendors/Form').then((m) => ({ default: m.VendorFormPage })));
const OrdersListPage = lazy(() => import('../pages/Orders/List').then((m) => ({ default: m.OrdersListPage })));
const OrderCreatePage = lazy(() => import('../pages/Orders/Create').then((m) => ({ default: m.OrderCreatePage })));
const OrderDetailPage = lazy(() => import('../pages/Orders/Detail').then((m) => ({ default: m.OrderDetailPage })));
const PastOrdersPage = lazy(() => import('../pages/Orders/PastOrders').then((m) => ({ default: m.PastOrdersPage })));
const NotificationsPage = lazy(() => import('../pages/Notifications/Index').then((m) => ({ default: m.NotificationsPage })));
const ApprovalsPage = lazy(() => import('../pages/Approvals/Index').then((m) => ({ default: m.ApprovalsPage })));
const ReportsPage = lazy(() => import('../pages/Reports').then((m) => ({ default: m.ReportsPage })));
const WeeklyReportPage = lazy(() => import('../pages/Reports/Weekly').then((m) => ({ default: m.WeeklyReportPage })));
const ImportsPage = lazy(() => import('../pages/Imports/Index').then((m) => ({ default: m.ImportsPage })));
const NotFoundPage = lazy(() => import('../pages/Stubs').then((m) => ({ default: m.NotFoundPage })));
const ForgotPassword = lazy(() => import('../pages/Auth/ForgotPassword').then((m) => ({ default: m.default })));
const PasswordReset = lazy(() => import('../pages/Auth/PasswordReset').then((m) => ({ default: m.default })));

const RouteFallback: React.FC = () => (
  <div className="flex items-center justify-center min-h-screen bg-gray-50">
    <div className="text-center">
      <div className="inline-block w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full animate-spin" />
      <p className="mt-3 text-sm text-gray-600">Loading…</p>
    </div>
  </div>
);

export const AppRouter: React.FC = () => {
  return (
    <>
      <Suspense fallback={<RouteFallback />}>
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<PasswordReset />} />

        {/* Protected Routes with AppShell */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <AppShell>
                <DashboardPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/inventory"
          element={
            <ProtectedRoute>
              <AppShell>
                <InventoryListPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/inventory/new"
          element={
            <ProtectedRoute>
              <AppShell>
                <InventoryFormPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/inventory/:id"
          element={
            <ProtectedRoute>
              <AppShell>
                <InventoryDetailPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/vendors"
          element={
            <ProtectedRoute>
              <AppShell>
                <VendorsListPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/vendors/new"
          element={
            <ProtectedRoute>
              <AppShell>
                <VendorFormPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/vendors/:id"
          element={
            <ProtectedRoute>
              <AppShell>
                <VendorDetailPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/orders"
          element={
            <ProtectedRoute>
              <AppShell>
                <OrdersListPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/orders/new"
          element={
            <ProtectedRoute>
              <AppShell>
                <OrderCreatePage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/orders/past"
          element={
            <ProtectedRoute>
              <AppShell>
                <PastOrdersPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/orders/:id"
          element={
            <ProtectedRoute>
              <AppShell>
                <OrderDetailPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/settings"
          element={
            <ProtectedRoute allowedRoles={["admin"]}>
              <AppShell>
                <SettingsPageComplete />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/notifications"
          element={
            <ProtectedRoute>
              <AppShell>
                <NotificationsPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/approvals"
          element={
            <ProtectedRoute>
              <AppShell>
                <ApprovalsPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/reports"
          element={
            <ProtectedRoute>
              <AppShell>
                <ReportsPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/reports/weekly"
          element={
            <ProtectedRoute>
              <AppShell>
                <WeeklyReportPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/imports"
          element={
            <ProtectedRoute>
              <AppShell>
                <ImportsPage />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route path="*" element={<NotFoundPage />} />
      </Routes>
      </Suspense>
    </>
  );
};

export default AppRouter;
