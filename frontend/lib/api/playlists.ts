import { apiClient } from "./client";
import type { Playlist, PlaylistItem, PaginatedData } from "@/types";

/**
 * Playlists API
 */

export interface PlaylistListParams {
  page?: number;
  page_size?: number;
  search?: string;
  is_active?: boolean;
  sort_by?: "created_at" | "name";
  sort_order?: "asc" | "desc";
}

export interface PlaylistCreate {
  name: string;
  is_active?: boolean;
  loop_mode?: boolean;
  shuffle_mode?: boolean;
  transition_type?: string;
  transition_duration_ms?: number;
  schedule_config?: Record<string, unknown>;
}

export interface PlaylistItemCreate {
  asset_id: string;
  duration: number;
}

export const playlistsApi = {
  /**
   * List playlists with pagination and filters
   */
  list: async (params?: PlaylistListParams): Promise<PaginatedData<Playlist>> => {
    const response = await apiClient.get<PaginatedData<Playlist>>("/api/v1/playlists", { params });
    return response.data;
  },

  /**
   * Get a single playlist by ID with items
   */
  get: async (id: string): Promise<Playlist> => {
    const response = await apiClient.get<Playlist>(`/api/v1/playlists/${id}`);
    return response.data;
  },

  /**
   * Create a new playlist
   */
  create: async (data: PlaylistCreate): Promise<Playlist> => {
    const response = await apiClient.post<Playlist>("/api/v1/playlists", data);
    return response.data;
  },

  /**
   * Update a playlist
   */
  update: async (
    id: string,
    data: Partial<
      Pick<Playlist, "name" | "is_active" | "loop_mode" | "shuffle_mode" | "transition_type" | "transition_duration_ms" | "schedule_config">
    >
  ): Promise<Playlist> => {
    const response = await apiClient.patch<Playlist>(`/api/v1/playlists/${id}`, data);
    return response.data;
  },

  /**
   * Delete a playlist
   */
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/playlists/${id}`);
  },

  /**
   * Add an item to a playlist
   */
  addItem: async (id: string, data: PlaylistItemCreate): Promise<PlaylistItem> => {
    const response = await apiClient.post<PlaylistItem>(`/api/v1/playlists/${id}/items`, data);
    return response.data;
  },

  /**
   * Update a playlist item
   */
  updateItem: async (id: string, itemId: string, data: Partial<Pick<PlaylistItem, "duration" | "order">>): Promise<PlaylistItem> => {
    const response = await apiClient.patch<PlaylistItem>(`/api/v1/playlists/${id}/items/${itemId}`, data);
    return response.data;
  },

  /**
   * Remove an item from a playlist
   */
  removeItem: async (id: string, itemId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/playlists/${id}/items/${itemId}`);
  },

  /**
   * Reorder playlist items
   */
  reorderItems: async (id: string, items: Array<{ id: string; order: number }>): Promise<PlaylistItem[]> => {
    const response = await apiClient.post<PlaylistItem[]>(`/api/v1/playlists/${id}/items/reorder`, { items });
    return response.data;
  },

  /**
   * Assign playlist to devices
   */
  assignToDevices: async (id: string, deviceIds: string[]): Promise<void> => {
    await apiClient.post(`/api/v1/playlists/${id}/assign`, { device_ids: deviceIds });
  },

  /**
   * Unassign playlist from devices
   */
  unassignFromDevices: async (id: string, deviceIds: string[]): Promise<void> => {
    await apiClient.post(`/api/v1/playlists/${id}/unassign`, { device_ids: deviceIds });
  },
};
