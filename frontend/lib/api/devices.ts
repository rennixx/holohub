import { apiClient } from "./client";
import type { Device, DeviceHeartbeat, PaginatedData } from "@/types";

/**
 * Devices API
 */

export interface DeviceListParams {
  page?: number;
  page_size?: number;
  search?: string;
  status?: string;
  sort_by?: "created_at" | "name" | "last_heartbeat";
  sort_order?: "asc" | "desc";
}

export interface DeviceCommand {
  command: "restart" | "clear_cache" | "screenshot" | "update_playlist";
  params?: Record<string, unknown>;
}

export const devicesApi = {
  /**
   * List devices with pagination and filters
   */
  list: async (params?: DeviceListParams): Promise<PaginatedData<Device>> => {
    const response = await apiClient.get<PaginatedData<Device>>("/api/v1/devices", { params });
    return response.data;
  },

  /**
   * Get a single device by ID
   */
  get: async (id: string): Promise<Device> => {
    const response = await apiClient.get<Device>(`/api/v1/devices/${id}`);
    return response.data;
  },

  /**
   * Register a new device
   */
  register: async (data: {
    name: string;
    hardware_type: string;
    hardware_id: string;
    location_metadata?: Record<string, unknown>;
    tags?: string[];
  }): Promise<Device> => {
    const response = await apiClient.post<Device>("/api/v1/devices", data);
    return response.data;
  },

  /**
   * Update a device
   */
  update: async (
    id: string,
    data: Partial<Pick<Device, "name" | "status" | "location_metadata" | "tags" | "display_config">>
  ): Promise<Device> => {
    const response = await apiClient.patch<Device>(`/api/v1/devices/${id}`, data);
    return response.data;
  },

  /**
   * Delete a device
   */
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/devices/${id}`);
  },

  /**
   * Send a command to a device
   */
  sendCommand: async (id: string, command: DeviceCommand): Promise<{ success: boolean; message?: string }> => {
    const response = await apiClient.post(`/api/v1/devices/${id}/command`, command);
    return response.data;
  },

  /**
   * Get device health metrics
   */
  getHealth: async (id: string, params?: { start_date?: string; end_date?: string }): Promise<DeviceHeartbeat[]> => {
    const response = await apiClient.get<DeviceHeartbeat[]>(`/api/v1/devices/${id}/health`, { params });
    return response.data;
  },

  /**
   * Get device logs
   */
  getLogs: async (id: string, params?: { limit?: number; offset?: number }): Promise<unknown> => {
    const response = await apiClient.get(`/api/v1/devices/${id}/logs`, { params });
    return response.data;
  },

  /**
   * Get assigned playlists for a device
   */
  getPlaylists: async (id: string): Promise<unknown> => {
    const response = await apiClient.get(`/api/v1/devices/${id}/playlists`);
    return response.data;
  },
};
