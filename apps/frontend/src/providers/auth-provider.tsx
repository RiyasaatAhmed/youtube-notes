/**
 * Authentication Provider
 *
 * Provides authentication state and user information throughout the application
 * using React Context API and React Query
 */

import { useCallback, useMemo, type ReactNode } from "react";
import {
  useCurrentUser,
  useLoginMutation,
  useLogoutMutation,
  useRegisterMutation,
  type LoginRequest,
  type RegisterRequest,
} from "@/api/auth";
import { AuthContext, type AuthContextValue } from "../contexts/auth-context";

/**
 * Auth Provider Props
 */
interface AuthProviderProps {
  children: ReactNode;
}

/**
 * Authentication Provider Component
 */
export function AuthProvider({ children }: AuthProviderProps) {
  // Fetch current user
  const {
    data: user = null,
    isLoading,
    error,
    refetch,
  } = useCurrentUser({
    retry: false,
    refetchOnMount: "always",
    refetchOnWindowFocus: true,
  });

  // Authentication mutations
  const loginMutation = useLoginMutation();
  const logoutMutation = useLogoutMutation();
  const registerMutation = useRegisterMutation();

  /**
   * Login function
   */
  const login = useCallback(
    async (credentials: LoginRequest) => {
      try {
        await loginMutation.mutateAsync(credentials);
        // User data will be automatically updated by the mutation's onSuccess
      } catch (error) {
        console.error("Login failed:", error);
        throw error;
      }
    },
    [loginMutation]
  );

  /**
   * Logout function
   */
  const logout = useCallback(async () => {
    try {
      await logoutMutation.mutateAsync();
      // Query cache will be cleared by the mutation's onSuccess
    } catch (error) {
      console.error("Logout failed:", error);
      throw error;
    }
  }, [logoutMutation]);

  /**
   * Register function
   */
  const register = useCallback(
    async (userData: RegisterRequest) => {
      try {
        await registerMutation.mutateAsync(userData);
        // User data will be automatically updated by the mutation's onSuccess
      } catch (error) {
        console.error("Registration failed:", error);
        throw error;
      }
    },
    [registerMutation]
  );

  /**
   * Refetch user data
   */
  const refetchUser = useCallback(async () => {
    try {
      await refetch();
    } catch (error) {
      console.error("Failed to refetch user:", error);
    }
  }, [refetch]);

  /**
   * Derived state: check if user is authenticated
   */
  const isAuthenticated = useMemo(() => {
    return user !== null && user !== undefined;
  }, [user]);

  /**
   * Context value
   */
  const contextValue = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated,
      isLoading,
      error: error as Error | null,
      loginLoading: loginMutation.isPending ?? false,
      logoutLoading: logoutMutation.isPending ?? false,
      registerLoading: registerMutation.isPending ?? false,
      login,
      logout,
      register,
      refetchUser,
    }),
    [
      user,
      isAuthenticated,
      isLoading,
      error,
      loginMutation.isPending,
      logoutMutation.isPending,
      registerMutation.isPending,
      login,
      logout,
      register,
      refetchUser,
    ]
  );

  return (
    <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>
  );
}
