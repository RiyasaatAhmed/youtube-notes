/**
 * Authentication Context
 *
 * Defines the authentication context and its types
 */

import { createContext } from "react";
import type { User, LoginRequest, RegisterRequest } from "@/api/auth";

/**
 * Authentication context value type
 */
export interface AuthContextValue {
  // User state
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  loginLoading: boolean;
  logoutLoading: boolean;
  registerLoading: boolean;
  error: Error | null;

  // Authentication actions
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  register: (userData: RegisterRequest) => Promise<void>;

  // Utility functions
  refetchUser: () => Promise<void>;
}

/**
 * Authentication context
 */
export const AuthContext = createContext<AuthContextValue | undefined>(
  undefined
);
