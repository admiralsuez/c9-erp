import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Button, ListLoadingState, ListEmptyState } from '../../components/ui';
import { useNotifications, useMarkNotificationRead, useMarkAllNotificationsRead } from '../../hooks/useNotifications';
import { formatDateTime } from '../../utils/format';
import { Bell, CheckCheck, ArrowLeft, Eye } from 'lucide-react';

export const NotificationsPage: React.FC = () => {
  const navigate = useNavigate();
  const { data: notifications, isLoading } = useNotifications();
  const markRead = useMarkNotificationRead();
  const markAllRead = useMarkAllNotificationsRead();

  const handleClick = (n: any) => {
    if (!n.is_read) {
      markRead.mutate(n.id);
    }
    if (n.type === 'approval_required') {
      navigate('/approvals');
    } else if (n.related_entity_type === 'order' && n.related_entity_id) {
      navigate(`/orders/${n.related_entity_id}`);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate(-1)} className="p-2 hover:bg-neutral-100 rounded-lg">
            <ArrowLeft className="w-5 h-5 text-neutral-600" />
          </button>
          <h1 className="text-3xl font-bold text-neutral-900">Notifications</h1>
        </div>
        {notifications && notifications.some((n: any) => !n.is_read) && (
          <Button
            variant="secondary"
            size="sm"
            onClick={() => markAllRead.mutate()}
            disabled={markAllRead.isPending}
          >
            <CheckCheck className="w-4 h-4" />
            Mark All Read
          </Button>
        )}
      </div>

      {isLoading ? (
        <ListLoadingState message="Loading notifications..." />
      ) : !notifications || notifications.length === 0 ? (
        <ListEmptyState icon={<Bell className="w-12 h-12 text-neutral-300 mx-auto mb-3" />} message="No notifications" />
      ) : (
        <div className="space-y-2">
          {notifications.map((n: any) => (
            <Card
              key={n.id}
              padding="md"
              className={`cursor-pointer hover:shadow-sm transition-shadow ${!n.is_read ? 'bg-primary-50/50 border-primary-200' : ''}`}
              onClick={() => handleClick(n)}
            >
              <div className="flex items-start gap-3">
                <div className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${n.is_read ? 'bg-neutral-300' : 'bg-primary-600'}`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <p className={`text-sm ${n.is_read ? 'text-neutral-600' : 'font-semibold text-neutral-900'}`}>
                      {n.title}
                    </p>
                    <span className="text-xs text-neutral-500 flex-shrink-0">
                      {formatDateTime(n.created_at)}
                    </span>
                  </div>
                  {n.actor_name && (
                    <p className="text-xs text-neutral-400 mt-0.5">by {n.actor_name}</p>
                  )}
                  {n.message && (
                    <p className="text-xs text-neutral-500 mt-0.5">{n.message}</p>
                  )}
                </div>
                {!n.is_read && (
                  <Eye className="w-4 h-4 text-primary-600 flex-shrink-0 mt-1" />
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default NotificationsPage;
