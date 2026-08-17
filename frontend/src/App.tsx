import React from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './context/AuthContext';
import { CompactModeProvider } from './contexts/CompactModeContext';
import { AppRouter } from './router';
import { queryClient } from './lib/queryClient';
import { ErrorBoundary } from './components/ErrorBoundary';

const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <CompactModeProvider>
            <AppRouter />
            <Toaster
              position="top-right"
              toastOptions={{
                duration: 4000,
                style: { fontSize: '14px' },
              }}
            />
          </CompactModeProvider>
        </AuthProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
};

export default App;
