/**
 * API Service
 *
 * Axios-based HTTP client service with interceptors, error handling, and enhanced features
 */

import axios from "axios";
import { BASE_URL } from "@/constants/api";
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse } from "axios";

// Create axios instance with cookie-based authentication
const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 60 * 5 * 1000, // 5 minutes
  withCredentials: true, // Automatically send cookies with requests
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor for logging and debugging
apiClient.interceptors.request.use(
  (config) => {
    // Log requests in development
    if (import.meta.env.DEV) {
      console.log(
        `📤 API Request: ${config.method?.toUpperCase()} ${config.url}`
      );
    }
    return config;
  },
  (error) => {
    console.error("❌ Request Error:", error);
    return Promise.reject(error);
  }
);

// Response interceptor for handling common errors
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // Log successful responses in development
    if (import.meta.env.DEV) {
      console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    }
    return response;
  },
  (error) => {
    // Handle common error cases
    if (error.response) {
      const { status, data } = error.response;

      switch (status) {
        case 401:
          // Unauthorized - redirect to login
          console.warn("🔐 Unauthorized, redirecting to login...");
          // Clear any stale auth data
          if (window.location.pathname !== "/log-in") {
            window.location.href = "/log-in";
          }
          break;
        case 403:
          // Forbidden - user doesn't have permission
          console.error(
            "🚫 Access forbidden:",
            data?.detail || data?.message || "Insufficient permissions"
          );
          break;
        case 404:
          // Not found
          console.error(
            "🔍 Resource not found:",
            data?.detail || data?.message || "Requested resource not found"
          );
          break;
        case 422:
          // Validation error
          console.error(
            "📝 Validation error:",
            data?.detail || data?.message || "Invalid data provided"
          );
          break;
        case 429:
          // Rate limited
          console.error(
            "⏰ Rate limited:",
            data?.detail || data?.message || "Too many requests"
          );
          break;
        case 500:
          // Server error
          console.error(
            "💥 Server error:",
            data?.detail || data?.message || "Internal server error"
          );
          break;
        default:
          console.error(
            `❌ API Error (${status}):`,
            data?.detail || data?.message || "Unknown error occurred"
          );
      }
    } else if (error.request) {
      // Network error
      console.error("🌐 Network error:", error.message);
    } else {
      // Other error
      console.error("❌ Error:", error.message);
    }
    return Promise.reject(error);
  }
);

// API service class with enhanced features
class ApiService {
  private client: AxiosInstance;

  constructor(client: AxiosInstance) {
    this.client = client;
  }

  /**
   * Generic GET request
   * @param url - API endpoint URL
   * @param config - Optional axios config
   * @returns Promise with response data
   */
  async get<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(url, config);
    return response.data;
  }

  /**
   * Generic POST request
   * @param url - API endpoint URL
   * @param data - Request body data
   * @param config - Optional axios config
   * @returns Promise with response data
   */
  async post<T = unknown>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const response = await this.client.post<T>(url, data, config);
    return response.data;
  }

  /**
   * Generic PUT request
   * @param url - API endpoint URL
   * @param data - Request body data
   * @param config - Optional axios config
   * @returns Promise with response data
   */
  async put<T = unknown>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const response = await this.client.put<T>(url, data, config);
    return response.data;
  }

  /**
   * Generic PATCH request
   * @param url - API endpoint URL
   * @param data - Request body data
   * @param config - Optional axios config
   * @returns Promise with response data
   */
  async patch<T = unknown>(
    url: string,
    data?: unknown,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const response = await this.client.patch<T>(url, data, config);
    return response.data;
  }

  /**
   * Generic DELETE request
   * @param url - API endpoint URL
   * @param config - Optional axios config
   * @returns Promise with response data
   */
  async delete<T = unknown>(
    url: string,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const response = await this.client.delete<T>(url, config);
    return response.data;
  }

  /**
   * Upload file with progress tracking
   * @param url - Upload endpoint URL
   * @param file - File to upload
   * @param onProgress - Progress callback (0-100)
   * @param config - Optional axios config
   * @returns Promise with response data
   */
  async upload<T = unknown>(
    url: string,
    file: File,
    onProgress?: (progress: number) => void,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await this.client.post<T>(url, formData, {
      ...config,
      headers: {
        "Content-Type": "multipart/form-data",
        ...config?.headers,
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress(progress);
        }
      },
    });
    return response.data;
  }

  /**
   * Upload multiple files with progress tracking
   * @param url - Upload endpoint URL
   * @param files - Files to upload
   * @param onProgress - Progress callback (0-100)
   * @param config - Optional axios config
   * @returns Promise with response data
   */
  async uploadMultiple<T = unknown>(
    url: string,
    files: File[],
    onProgress?: (progress: number) => void,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const formData = new FormData();
    files.forEach((file, index) => {
      formData.append(`file${index}`, file);
    });

    const response = await this.client.post<T>(url, formData, {
      ...config,
      headers: {
        "Content-Type": "multipart/form-data",
        ...config?.headers,
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress(progress);
        }
      },
    });
    return response.data;
  }

  /**
   * Download file
   * @param url - Download endpoint URL
   * @param filename - Optional filename for downloaded file
   */
  async download(url: string, filename?: string): Promise<void> {
    const response = await this.client.get(url, {
      responseType: "blob",
    });

    const blob = new Blob([response.data]);
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = downloadUrl;
    link.download = filename || "download";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  }

  /**
   * Health check endpoint
   * @returns Promise with boolean indicating health status
   */
  async healthCheck(): Promise<boolean> {
    try {
      await this.client.get("/health");
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Get base URL
   * @returns Current base URL
   */
  getBaseURL(): string {
    return this.client.defaults.baseURL || "";
  }

  /**
   * Set base URL
   * @param url - New base URL
   */
  setBaseURL(url: string): void {
    this.client.defaults.baseURL = url;
  }

  /**
   * Get axios instance for advanced usage
   * @returns Axios instance
   */
  getClient(): AxiosInstance {
    return this.client;
  }
}

// Create and export singleton instance
const apiService = new ApiService(apiClient);

export default apiService;
export { apiClient };
