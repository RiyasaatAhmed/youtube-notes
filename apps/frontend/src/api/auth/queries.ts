/**
 * Authentication Queries
 *
 * React Query hooks for fetching authentication data
 */

import { useQuery, type UseQueryOptions } from "@tanstack/react-query";
import AuthService from "./auth-service";
import type { User } from "@/types/auth.types";

/**
 * Query keys for authentication
 */
export const AUTH_QUERY_KEYS = {
  currentUser: ["auth", "currentUser"] as const,
  isAuthenticated: ["auth", "isAuthenticated"] as const,
} as const;

/**
 * Hook to get current authenticated user
 *
 * @example
 * ```tsx
 * const { data: user, isLoading, error } = useCurrentUser()
 * ```
 */
export const useCurrentUser = (
  options?: Omit<UseQueryOptions<User, Error>, "queryKey" | "queryFn">
) => {
  return useQuery<User, Error>({
    queryKey: AUTH_QUERY_KEYS.currentUser,
    queryFn: AuthService.getCurrentUser,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
    retry: false, // Don't retry on 401
    refetchOnWindowFocus: true,
    refetchOnMount: true,
    ...options,
  });
};

/**
 * Hook to check if user is authenticated
 *
 * @example
 * ```tsx
 * const { data: isAuthenticated, isLoading } = useIsAuthenticated()
 * if (isLoading) return <div>Loading...</div>
 * if (isAuthenticated) return <div>Authenticated</div>
 * ```
 */
export const useIsAuthenticated = (
  options?: Omit<UseQueryOptions<boolean, Error>, "queryKey" | "queryFn">
) => {
  return useQuery<boolean, Error>({
    queryKey: AUTH_QUERY_KEYS.isAuthenticated,
    queryFn: AuthService.isAuthenticated,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    retry: false,
    ...options,
  });
};
