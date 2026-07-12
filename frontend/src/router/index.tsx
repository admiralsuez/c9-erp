import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AppShell } from '../layouts/AppShell';
import { ProtectedRoute } from '../components/ProtectedRoute';
import { LoginPage } from '../pages/Login';
import { DashboardPage } from '../pages/Dashboard';
import { InventoryListPage } from '../pages/Inventory/List';
import { InventoryDetailPage } from '../pages/Inventory/Detail';
import { InventoryFormPage } from '../pages/Inventory/Form';
import { SettingsPageComplete } from '../pages/Settings/SettingsComplete';
import { VendorsListPage } from '../pages/Vendors/List';
import { VendorDetailPage } from '../pages/Vendors/Detail';
import { VendorFormPage } from '../pages/Vendors/Form';
import { OrdersListPage } from '../pages/Orders/List';
import { OrderCreatePage } from '../pages/Orders/Create';
import { OrderDetailPage } from '../pages/Orders/Detail';
import { NotificationsPage } from '../pages/Notifications/Index';
import { ApprovalsPage } from '../pages/Approvals/Index';
import { ReportsPage } from '../pages/Reports';
import { NotFoundPage } from '../pages/Stubs';

export const AppRouter: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<LoginPage />} />

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
            <ProtectedRoute>
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

        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
};

export default AppRouter;
