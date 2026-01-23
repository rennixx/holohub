import axios, { type AxiosError, type AxiosInstance, type InternalAxiosRequestConfig, type AxiosResponse } from "axios";
import { useAuthStore } from "@/lib/store";
import { toast } from "sonner";

/**
 * API Client Configuration
 * Handles base URL, timeouts, and default headers
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Create axios instance
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: 30000, // 30 seconds
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Request Interceptor
 * Adds authentication token to all outgoing requests
 */
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Skip auth for auth endpoints
    const isAuthEndpoint = config.url?.includes("/auth/");
    const isTokenEndpoint = config.url?.includes("/auth/token");

    if (!isAuthEndpoint && !isTokenEndpoint) {
      const accessToken = useAuthStore.getState().accessToken;
      if (accessToken) {
        config.headers.Authorization = `Bearer ${accessToken}`;
      }
    }

    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

/**
 * Response Interceptor
 * Handles token refresh and error responses
 */
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  async (error: AxiosError<unknown>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Handle 401 Unauthorized - Token refresh
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshToken = useAuthStore.getState().refreshToken;

      if (refreshToken) {
        try {
          // Try to refresh the token
          const response = await axios.post(
            `${API_URL}/api/v1/auth/refresh`,
            { refresh_token: refreshToken },
            { headers: { "Content-Type": "application/json" } }
          );

          const { access_token, refresh_token: newRefreshToken } = response.data;

          // Update tokens in store
          useAuthStore.getState().updateTokens({
            access_token,
            refresh_token: newRefreshToken || refreshToken,
            token_type: "bearer",
            expires_in: 900, // 15 minutes
          });

          // Update Authorization header and retry
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return apiClient(originalRequest);
        } catch (refreshError) {
          // Refresh failed - clear auth and redirect to login
          useAuthStore.getState().clearAuth();

          // Only redirect if we're in the browser
          if (typeof window !== "undefined") {
            toast.error("Session expired. Please log in again.");
            window.location.href = "/login";
          }

          return Promise.reject(refreshError);
        }
      } else {
        // No refresh token - clear auth
        useAuthStore.getState().clearAuth();

        if (typeof window !== "undefined") {
          toast.error("Please log in to continue.");
          window.location.href = "/login";
        }
      }
    }

    // Handle other errors
    if (error.response) {
      const status = error.response.status;
      const data = error.response.data as { detail?: string; message?: string };

      switch (status) {
        case 400:
          toast.error(data?.detail || data?.message || "Invalid request");
          break;
        case 403:
          toast.error(data?.detail || "You don't have permission to perform this action");
          break;
        case 404:
          toast.error(data?.detail || "Resource not found");
          break;
        case 429:
          toast.error("Too many requests. Please try again later.");
          break;
        case 500:
          toast.error("Server error. Please try again later.");
          break;
        default:
          toast.error(data?.detail || "An unexpected error occurred");
      }
    } else if (error.request) {
      // Network error
      toast.error("Network error. Please check your connection.");
    }

    return Promise.reject(error);
  }
);

export default apiClient;
