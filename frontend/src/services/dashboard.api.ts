/**
 * Dashboard API Service
 *
 * API client for fetching role-based dashboard data.
 * Handles authentication, error handling, and type safety.
 */

import apiClient from '../lib/axios';
import type {
  DashboardResponse,
  DashboardStatsRequest,
  DashboardCounts,
} from '../types/dashboard';

/**
 * API endpoints
 */
const DASHBOARD_ENDPOINTS = {
  STATS: '/dashboard/stats',
  COUNTS: '/dashboard/counts',
  HEALTH: '/dashboard/health',
} as const;

/**
 * Error response from API
 */
interface ApiError {
  detail: string;
}

/**
 * Dashboard API error with details
 */
export class DashboardApiError extends Error {
  public statusCode: number;
  public detail: string;

  constructor(message: string, statusCode: number, detail: string) {
    super(message);
    this.name = 'DashboardApiError';
    this.statusCode = statusCode;
    this.detail = detail;
  }
}

/**
 * Get dashboard statistics based on authenticated user's role.
 *
 * This is the main endpoint that returns role-specific dashboard data.
 *
 * @param params - Optional request parameters
 * @param params.include_recent - Include recent items (default: true)
 * @param params.recent_limit - Limit for recent items (1-50, default: 10)
 * @returns Promise resolving to role-specific dashboard data
 * @throws {DashboardApiError} If the request fails
 *
 * @example
 * ```typescript
 * // Fetch dashboard with default settings
 * const dashboard = await getDashboardStats();
 *
 * // Fetch with custom settings
 * const dashboard = await getDashboardStats({
 *   include_recent: true,
 *   recent_limit: 20
 * });
 *
 * // Type-safe access based on role
 * if (dashboard.role === 'admin') {
 *   console.log(dashboard.company); // TypeScript knows this exists
 * }
 * ```
 */
export const getDashboardStats = async (
  params?: DashboardStatsRequest
): Promise<DashboardResponse> => {
  try {
    console.log('[Dashboard API] Fetching dashboard stats...', {
      endpoint: DASHBOARD_ENDPOINTS.STATS,
      params: {
        include_recent: params?.include_recent ?? true,
        recent_limit: params?.recent_limit ?? 10,
      },
      baseURL: apiClient.defaults.baseURL,
    });

    const response = await apiClient.get<DashboardResponse>(
      DASHBOARD_ENDPOINTS.STATS,
      {
        params: {
          include_recent: params?.include_recent ?? true,
          recent_limit: params?.recent_limit ?? 10,
        },
      }
    );

    console.log('[Dashboard API] Success:', response.data);
    return response.data;
  } catch (error: any) {
    // Enhanced error logging
    console.error('[Dashboard API] Error details:', {
      message: error.message,
      response: error.response?.data,
      status: error.response?.status,
      request: error.request ? 'Request was made' : 'No request',
      config: error.config ? {
        url: error.config.url,
        method: error.config.method,
        baseURL: error.config.baseURL,
      } : 'No config',
    });

    // Handle axios error
    if (error.response) {
      const apiError = error.response.data as ApiError;
      throw new DashboardApiError(
        'Failed to fetch dashboard statistics',
        error.response.status,
        apiError.detail || error.message
      );
    } else if (error.request) {
      // Request was made but no response received
      throw new DashboardApiError(
        'No response from server',
        0,
        `Сервер не отвечает. Проверьте что backend запущен на ${apiClient.defaults.baseURL}`
      );
    } else {
      // Something else happened
      throw new DashboardApiError(
        'Request failed',
        0,
        error.message || 'An unknown error occurred'
      );
    }
  }
};

/**
 * Get dashboard counts only (lightweight, faster endpoint).
 *
 * This endpoint returns only aggregated counts without detailed data.
 * Useful for quick stats display or mobile apps.
 *
 * @returns Promise resolving to dashboard counts with user role
 * @throws {DashboardApiError} If the request fails
 *
 * @example
 * ```typescript
 * const counts = await getDashboardCounts();
 * console.log(`Total users: ${counts.users}`);
 * console.log(`Active users: ${counts.active_users}`);
 * ```
 */
export const getDashboardCounts = async (): Promise<
  DashboardCounts & { role: string }
> => {
  try {
    const response = await apiClient.get<DashboardCounts & { role: string }>(
      DASHBOARD_ENDPOINTS.COUNTS
    );

    return response.data;
  } catch (error: any) {
    if (error.response) {
      const apiError = error.response.data as ApiError;
      throw new DashboardApiError(
        'Failed to fetch dashboard counts',
        error.response.status,
        apiError.detail || error.message
      );
    } else if (error.request) {
      throw new DashboardApiError(
        'No response from server',
        0,
        'The server did not respond. Please check your connection.'
      );
    } else {
      throw new DashboardApiError(
        'Request failed',
        0,
        error.message || 'An unknown error occurred'
      );
    }
  }
};

/**
 * Check dashboard service health.
 *
 * This endpoint doesn't require authentication and can be used
 * for health checks and monitoring.
 *
 * @returns Promise resolving to service health status
 * @throws {DashboardApiError} If the request fails
 *
 * @example
 * ```typescript
 * const health = await checkDashboardHealth();
 * console.log(health.status); // "healthy"
 * ```
 */
export const checkDashboardHealth = async (): Promise<{
  status: string;
  service: string;
  message: string;
}> => {
  try {
    const response = await apiClient.get(DASHBOARD_ENDPOINTS.HEALTH);
    return response.data;
  } catch (error: any) {
    if (error.response) {
      const apiError = error.response.data as ApiError;
      throw new DashboardApiError(
        'Failed to check dashboard health',
        error.response.status,
        apiError.detail || error.message
      );
    } else {
      throw new DashboardApiError(
        'Request failed',
        0,
        error.message || 'An unknown error occurred'
      );
    }
  }
};

/**
 * React Query hook helper - Get query key for dashboard stats
 *
 * @param params - Optional request parameters
 * @returns Query key array for React Query
 *
 * @example
 * ```typescript
 * const queryKey = getDashboardStatsQueryKey({ recent_limit: 20 });
 * // ['dashboard', 'stats', { include_recent: true, recent_limit: 20 }]
 * ```
 */
export const getDashboardStatsQueryKey = (params?: DashboardStatsRequest) => {
  return [
    'dashboard',
    'stats',
    {
      include_recent: params?.include_recent ?? true,
      recent_limit: params?.recent_limit ?? 10,
    },
  ] as const;
};

/**
 * React Query hook helper - Get query key for dashboard counts
 *
 * @returns Query key array for React Query
 *
 * @example
 * ```typescript
 * const queryKey = getDashboardCountsQueryKey();
 * // ['dashboard', 'counts']
 * ```
 */
export const getDashboardCountsQueryKey = () => {
  return ['dashboard', 'counts'] as const;
};

/**
 * Helper function to handle dashboard API errors in components
 *
 * @param error - Error from API call
 * @returns User-friendly error message
 *
 * @example
 * ```typescript
 * try {
 *   await getDashboardStats();
 * } catch (error) {
 *   const message = handleDashboardError(error);
 *   toast.error(message);
 * }
 * ```
 */
export const handleDashboardError = (error: unknown): string => {
  if (error instanceof DashboardApiError) {
    // Map status codes to user-friendly messages
    switch (error.statusCode) {
      case 401:
        return 'Сессия истекла. Пожалуйста, войдите снова.';
      case 403:
        return 'У вас нет доступа к этим данным.';
      case 400:
        return `Ошибка запроса: ${error.detail}`;
      case 500:
        return 'Ошибка сервера. Пожалуйста, попробуйте позже.';
      case 0:
        return error.detail;
      default:
        return `Ошибка: ${error.detail}`;
    }
  } else if (error instanceof Error) {
    return error.message;
  } else {
    return 'Произошла неизвестная ошибка';
  }
};

/**
 * Cache configuration for dashboard data
 */
export const DASHBOARD_CACHE_CONFIG = {
  // Recommended cache time: 5-10 minutes
  staleTime: 5 * 60 * 1000, // 5 minutes
  cacheTime: 10 * 60 * 1000, // 10 minutes
  // Refetch on window focus for fresh data
  refetchOnWindowFocus: true,
  // Don't refetch on mount if data is fresh
  refetchOnMount: false,
  // Retry failed requests
  retry: 2,
} as const;

/**
 * Export all dashboard API functions
 */
export default {
  getDashboardStats,
  getDashboardCounts,
  checkDashboardHealth,
  getDashboardStatsQueryKey,
  getDashboardCountsQueryKey,
  handleDashboardError,
  DASHBOARD_CACHE_CONFIG,
};
