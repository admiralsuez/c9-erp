import React from 'react';
import { clsx } from 'clsx';
import { Loader, Inbox } from 'lucide-react';

interface ListItemProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  hoverable?: boolean;
}

export const ListItem: React.FC<ListItemProps> = ({ children, hoverable = false, className, ...props }) => (
  <div
    className={clsx(
      'flex items-center gap-3 p-3 bg-neutral-50 rounded-lg border border-neutral-100',
      hoverable && 'hover:bg-neutral-100 cursor-pointer transition-colors',
      className
    )}
    {...props}
  >
    {children}
  </div>
);

interface ListEmptyStateProps {
  icon?: React.ReactNode;
  message?: string;
}

export const ListEmptyState: React.FC<ListEmptyStateProps> = ({
  icon = <Inbox className="w-12 h-12 text-neutral-300 mx-auto mb-3" />,
  message = 'No items found',
}) => (
  <div className="text-center py-12">
    {icon}
    <p className="text-neutral-500">{message}</p>
  </div>
);

interface ListLoadingStateProps {
  message?: string;
}

export const ListLoadingState: React.FC<ListLoadingStateProps> = ({ message = 'Loading...' }) => (
  <div className="flex items-center justify-center min-h-64">
    <div className="flex flex-col items-center gap-2">
      <Loader className="w-6 h-6 animate-spin text-primary-600" />
      <p className="text-neutral-500">{message}</p>
    </div>
  </div>
);
