import { apiClient } from './client';

export const authApi = {
  /**
   * Request password reset - sends reset link to email
   */
  requestPasswordReset: async (data: { email: string }) => {
    const response = await apiClient.post('/auth/forgot-password', data);
    return response.data;
  },

  /**
   * Reset password with token
   */
  resetPassword: async (data: { token: string; new_password: string }) => {
    const response = await apiClient.post('/auth/reset-password', data);
    return response.data;
  },

  /**
   * Verify reset token
   */
  verifyResetToken: async (token: string) => {
    const response = await apiClient.get(`/auth/verify-reset-token?token=${token}`);
    return response.data;
  },
};
