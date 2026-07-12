import { apiClient } from './client';

export interface NotificationResponse {
  id: number;
  user_id: number;
  actor_id: number | null;
  actor_name: string | null;
  title: string;
  message: string | null;
  type: string;
  related_entity_type: string | null;
  related_entity_id: number | null;
  is_read: boolean;
  created_at: string;
}

export const notificationsApi = {
  list: async (unreadOnly: boolean = false): Promise<NotificationResponse[]> => {
    const response = await apiClient.get<NotificationResponse[]>(
      `/notifications?unread_only=${unreadOnly}&size=50`
    );
    return response.data;
  },

  unreadCount: async (): Promise<number> => {
    const response = await apiClient.get<{ count: number }>('/notifications/unread-count');
    return response.data.count;
  },

  markRead: async (notificationId: number): Promise<void> => {
    await apiClient.post(`/notifications/${notificationId}/read`);
  },

  markAllRead: async (): Promise<void> => {
    await apiClient.post('/notifications/mark-all-read');
  },
};
