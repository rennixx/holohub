/**
 * Settings API Client
 *
 * API functions for user and organization settings.
 */
import { apiClient } from "./client";
import type {
  UserSettings,
  UserSettingsUpdate,
  UserSettingsResponse,
  OrgSettings,
  OrgSettingsUpdate,
  OrgSettingsResponse,
  LogoUploadResponse,
} from "@/types/settings";

/**
 * User Settings API
 */
export const settingsApi = {
  /**
   * Get current user's settings
   */
  get: async (): Promise<UserSettingsResponse> => {
    const response = await apiClient.get<UserSettingsResponse>("/api/v1/settings");
    return response.data;
  },

  /**
   * Update current user's settings
   */
  update: async (data: UserSettingsUpdate): Promise<UserSettingsResponse> => {
    const response = await apiClient.put<UserSettingsResponse>("/api/v1/settings", data);
    return response.data;
  },

  /**
   * Partial update user settings (same as update for this API)
   */
  patch: async (data: UserSettingsUpdate): Promise<UserSettingsResponse> => {
    const response = await apiClient.patch<UserSettingsResponse>("/api/v1/settings", data);
    return response.data;
  },

  /**
   * Reset user settings to defaults
   */
  reset: async (): Promise<UserSettingsResponse> => {
    const response = await apiClient.post<UserSettingsResponse>("/api/v1/settings/reset");
    return response.data;
  },
};

/**
 * Organization Settings API
 */
export const orgSettingsApi = {
  /**
   * Get current organization's settings
   */
  get: async (): Promise<OrgSettingsResponse> => {
    const response = await apiClient.get<OrgSettingsResponse>("/api/v1/settings/organization");
    return response.data;
  },

  /**
   * Update current organization's settings
   */
  update: async (data: OrgSettingsUpdate): Promise<OrgSettingsResponse> => {
    const response = await apiClient.put<OrgSettingsResponse>("/api/v1/settings/organization", data);
    return response.data;
  },

  /**
   * Upload organization logo
   */
  uploadLogo: async (file: File): Promise<LogoUploadResponse> => {
    const formData = new FormData();
    formData.append("file", file);

    const response = await apiClient.post<LogoUploadResponse>(
      "/api/v1/settings/organization/logo",
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );
    return response.data;
  },

  /**
   * Delete organization logo
   */
  deleteLogo: async (): Promise<void> => {
    await apiClient.delete("/api/v1/settings/organization/logo");
  },
};
