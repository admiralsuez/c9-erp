import { apiClient } from './client';

export interface UserResponse {
  id: number;
  full_name: string;
  email: string;
  department?: string;
  role?: {
    id: number;
    name: string;
  };
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PaginatedUsersResponse {
  items: UserResponse[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export const usersApi = {
  list: async (page: number = 1, size: number = 100): Promise<PaginatedUsersResponse> => {
    const response = await apiClient.get<PaginatedUsersResponse>(
      `/users?page=${page}&size=${size}`
    );
    return response.data;
  },

  get: async (userId: number): Promise<UserResponse> => {
    const response = await apiClient.get<UserResponse>(`/users/${userId}`);
    return response.data;
  },
};
