import { apiClient } from "./client";
import type { Asset, PaginatedData } from "@/types";

/**
 * Assets API
 */

export interface AssetListParams {
  page?: number;
  page_size?: number;
  search?: string;
  category?: string;
  processing_status?: string;
  sort_by?: "created_at" | "title" | "file_size" | "duration";
  sort_order?: "asc" | "desc";
}

export interface AssetUploadResponse {
  id: string;
  upload_url: string;
  file_path: string;
}

export const assetsApi = {
  /**
   * List assets with pagination and filters
   */
  list: async (params?: AssetListParams): Promise<PaginatedData<Asset>> => {
    const response = await apiClient.get<PaginatedData<Asset>>("/api/v1/assets", { params });
    return response.data;
  },

  /**
   * Get a single asset by ID
   */
  get: async (id: string): Promise<Asset> => {
    const response = await apiClient.get<Asset>(`/api/v1/assets/${id}`);
    return response.data;
  },

  /**
   * Request an upload URL for a new asset
   */
  requestUpload: async (filename: string, fileSize: number, mimeType: string): Promise<AssetUploadResponse> => {
    const response = await apiClient.post<AssetUploadResponse>("/api/v1/assets/upload/request", {
      filename,
      file_size: fileSize,
      mime_type: mimeType,
    });
    return response.data;
  },

  /**
   * Upload file directly to S3/MinIO
   */
  uploadToS3: async (uploadUrl: string, file: File, onProgress?: (progress: number) => void): Promise<void> => {
    await apiClient.put(uploadUrl, file, {
      headers: { "Content-Type": file.type },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });
  },

  /**
   * Confirm upload and create asset record
   */
  confirmUpload: async (uploadId: string, data: { title: string; description?: string; category: string }): Promise<Asset> => {
    const response = await apiClient.post<Asset>("/api/v1/assets/upload/confirm", {
      upload_id: uploadId,
      ...data,
    });
    return response.data;
  },

  /**
   * Upload file directly through backend (no CORS issues)
   */
  uploadDirect: async (file: File, title: string, description?: string, onProgress?: (progress: number) => void): Promise<Asset> => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("title", title);
    if (description) {
      formData.append("description", description);
    }

    const response = await apiClient.post<Asset>("/api/v1/assets/upload/direct", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });
    return response.data;
  },

  /**
   * Update an asset
   */
  update: async (id: string, data: Partial<Pick<Asset, "title" | "description" | "category" | "metadata">>): Promise<Asset> => {
    const response = await apiClient.patch<Asset>(`/api/v1/assets/${id}`, data);
    return response.data;
  },

  /**
   * Delete an asset
   */
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/assets/${id}`);
  },

  /**
   * Request reprocessing of an asset
   */
  reprocess: async (id: string): Promise<Asset> => {
    const response = await apiClient.post<Asset>(`/api/v1/assets/${id}/reprocess`);
    return response.data;
  },

  /**
   * Get asset analytics
   */
  getAnalytics: async (id: string, params?: { start_date?: string; end_date?: string }): Promise<unknown> => {
    const response = await apiClient.get(`/api/v1/assets/${id}/analytics`, { params });
    return response.data;
  },
};
