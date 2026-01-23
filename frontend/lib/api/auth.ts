import { apiClient } from "./client";
import type { LoginRequest, RegisterRequest, AuthResponse, UserMe } from "@/types";

/**
 * Authentication API
 */

export const authApi = {
  /**
   * Login with email and password
   */
  login: async (data: LoginRequest): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>("/api/v1/auth/login", data);
    return response.data;
  },

  /**
   * Register a new organization and user
   */
  register: async (data: RegisterRequest): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>("/api/v1/auth/register", data);
    return response.data;
  },

  /**
   * Get current user profile
   */
  me: async (): Promise<UserMe> => {
    const response = await apiClient.get<UserMe>("/api/v1/auth/me");
    return response.data;
  },

  /**
   * Refresh access token
   */
  refresh: async (refreshToken: string): Promise<{ access_token: string; refresh_token?: string }> => {
    const response = await apiClient.post("/api/v1/auth/refresh", { refresh_token: refreshToken });
    return response.data;
  },

  /**
   * Logout (invalidate refresh token)
   */
  logout: async (refreshToken: string): Promise<void> => {
    await apiClient.post("/api/v1/auth/logout", { refresh_token: refreshToken });
  },

  /**
   * Setup MFA
   */
  setupMFA: async (): Promise<{ secret: string; qr_code: string; backup_codes: string[] }> => {
    const response = await apiClient.post("/api/v1/auth/mfa/setup");
    return response.data;
  },

  /**
   * Verify and enable MFA
   */
  verifyMFA: async (code: string): Promise<{ enabled: boolean }> => {
    const response = await apiClient.post("/api/v1/auth/mfa/verify", { code });
    return response.data;
  },

  /**
   * Disable MFA
   */
  disableMFA: async (password: string): Promise<{ disabled: boolean }> => {
    const response = await apiClient.post("/api/v1/auth/mfa/disable", { password });
    return response.data;
  },

  /**
   * Request password reset
   */
  requestPasswordReset: async (email: string): Promise<void> => {
    await apiClient.post("/api/v1/auth/password/reset-request", { email });
  },

  /**
   * Reset password with token
   */
  resetPassword: async (token: string, newPassword: string): Promise<void> => {
    await apiClient.post("/api/v1/auth/password/reset", { token, new_password: newPassword });
  },

  /**
   * OAuth2 token endpoint for Swagger UI
   */
  token: async (username: string, password: string): Promise<{ access_token: string; token_type: string }> => {
    const response = await apiClient.post("/api/v1/auth/token", new URLSearchParams({ username, password }), {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    return response.data;
  },
};
