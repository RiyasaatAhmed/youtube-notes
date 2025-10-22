/**
 * Authentication Mutations
 *
 * React Query hooks for authentication mutations
 */

import {
  useMutation,
  useQueryClient,
  type UseMutationOptions,
} from "@tanstack/react-query";
import AuthService from "./auth-service";
import { AUTH_QUERY_KEYS } from "./queries";
import type {
  User,
  RegisterRequest,
  LoginRequest,
  LoginResponse,
  TokenResponse,
  MessageResponse,
} from "@/types/auth.types";

/**
 * Hook for user registration
 *
 * @example
 * ```tsx
 * const registerMutation = useRegisterMutation()
 *
 * const handleRegister = async (data: RegisterRequest) => {
 *   try {
 *     const user = await registerMutation.mutateAsync(data)
 *     console.log('Registered:', user)
 *   } catch (error) {
 *     console.error('Registration failed:', error)
 *   }
 * }
 * ```
 */
export const useRegisterMutation = (
  options?: Omit<UseMutationOptions<User, Error, RegisterRequest>, "mutationFn">
) => {
  const queryClient = useQueryClient();

  return useMutation<User, Error, RegisterRequest>({
    mutationFn: AuthService.register,
    onSuccess: (user) => {
      queryClient.setQueryData(AUTH_QUERY_KEYS.currentUser, user);
      queryClient.setQueryData(AUTH_QUERY_KEYS.isAuthenticated, true);
    },
    ...options,
  });
};

/**
 * Hook for user login
 *
 * @example
 * ```tsx
 * const loginMutation = useLoginMutation()
 *
 * const handleLogin = async (credentials: LoginRequest) => {
 *   try {
 *     const response = await loginMutation.mutateAsync(credentials)
 *     console.log('Logged in:', response.user)
 *   } catch (error) {
 *     console.error('Login failed:', error)
 *   }
 * }
 * ```
 */
export const useLoginMutation = (
  options?: Omit<
    UseMutationOptions<LoginResponse, Error, LoginRequest>,
    "mutationFn"
  >
) => {
  const queryClient = useQueryClient();

  return useMutation<LoginResponse, Error, LoginRequest>({
    mutationFn: AuthService.login,
    onSuccess: (response) => {
      queryClient.setQueryData(AUTH_QUERY_KEYS.currentUser, response.user);
      queryClient.setQueryData(AUTH_QUERY_KEYS.isAuthenticated, true);
    },
    ...options,
  });
};

/**
 * Hook for user logout
 *
 * @example
 * ```tsx
 * const logoutMutation = useLogoutMutation()
 *
 * const handleLogout = async () => {
 *   try {
 *     await logoutMutation.mutateAsync()
 *     console.log('Logged out successfully')
 *   } catch (error) {
 *     console.error('Logout failed:', error)
 *   }
 * }
 * ```
 */
export const useLogoutMutation = (
  options?: Omit<UseMutationOptions<MessageResponse, Error, void>, "mutationFn">
) => {
  const queryClient = useQueryClient();

  return useMutation<MessageResponse, Error, void>({
    mutationFn: AuthService.logout,
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: AUTH_QUERY_KEYS.currentUser });
      queryClient.setQueryData(AUTH_QUERY_KEYS.isAuthenticated, false);

      queryClient.clear();
    },
    ...options,
  });
};

/**
 * Hook for refreshing access token
 *
 * @example
 * ```tsx
 * const refreshMutation = useRefreshTokenMutation()
 *
 * const handleRefresh = async () => {
 *   try {
 *     const response = await refreshMutation.mutateAsync()
 *     console.log('Token refreshed:', response.user)
 *   } catch (error) {
 *     console.error('Refresh failed:', error)
 *   }
 * }
 * ```
 */
export const useRefreshTokenMutation = (
  options?: Omit<UseMutationOptions<TokenResponse, Error, void>, "mutationFn">
) => {
  const queryClient = useQueryClient();

  return useMutation<TokenResponse, Error, void>({
    mutationFn: AuthService.refreshToken,
    onSuccess: (response) => {
      queryClient.setQueryData(AUTH_QUERY_KEYS.currentUser, response.user);
      queryClient.setQueryData(AUTH_QUERY_KEYS.isAuthenticated, true);
    },
    ...options,
  });
};
