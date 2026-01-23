import { apiClient } from "./client";
import type { User, PaginatedData } from "@/types";

/**
 * Users API
 */

export interface UserListParams {
  page?: number;
  page_size?: number;
  search?: string;
  role?: string;
  sort_by?: "created_at" | "name" | "email";
  sort_order?: "asc" | "desc";
}

export interface UserInvite {
  email: string;
  full_name: string;
  role: string;
}

export interface UserUpdate {
  full_name?: string;
  role?: string;
  is_active?: boolean;
}

export const usersApi = {
  /**
   * List users in the current organization
   */
  list: async (params?: UserListParams): Promise<PaginatedData<User>> => {
    const response = await apiClient.get<PaginatedData<User>>("/api/v1/users", { params });
    return response.data;
  },

  /**
   * Get a single user by ID
   */
  get: async (id: string): Promise<User> => {
    const response = await apiClient.get<User>(`/api/v1/users/${id}`);
    return response.data;
  },

  /**
   * Invite a new user to the organization
   */
  invite: async (data: UserInvite): Promise<User> => {
    const response = await apiClient.post<User>("/api/v1/users/invite", data);
    return response.data;
  },

  /**
   * Update a user
   */
  update: async (id: string, data: UserUpdate): Promise<User> => {
    const response = await apiClient.patch<User>(`/api/v1/users/${id}`, data);
    return response.data;
  },

  /**
   * Delete a user
   */
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/users/${id}`);
  },

  /**
   * Change user password
   */
  changePassword: async (data: { current_password: string; new_password: string }): Promise<void> => {
    await apiClient.post("/api/v1/users/me/password", data);
  },
};
