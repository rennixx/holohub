import { apiClient } from "./client";
import type { Organization, OrganizationStats } from "@/types";

/**
 * Organizations API
 */

export interface OrganizationUpdate {
  name?: string;
  branding?: Record<string, unknown>;
}

export const organizationsApi = {
  /**
   * Get current organization details
   */
  get: async (): Promise<Organization> => {
    const response = await apiClient.get<Organization>("/api/v1/organizations/current");
    return response.data;
  },

  /**
   * Update organization
   */
  update: async (data: OrganizationUpdate): Promise<Organization> => {
    const response = await apiClient.patch<Organization>("/api/v1/organizations/current", data);
    return response.data;
  },

  /**
   * Get organization statistics
   */
  getStats: async (): Promise<OrganizationStats> => {
    const response = await apiClient.get<OrganizationStats>("/api/v1/organizations/current/stats");
    return response.data;
  },

  /**
   * Get organization usage/billing info
   */
  getUsage: async (): Promise<unknown> => {
    const response = await apiClient.get("/api/v1/organizations/current/usage");
    return response.data;
  },
};
