/**
 * Authentication Module
 *
 * Exports all authentication-related functionality
 */

export { AuthService, default as authService } from "./auth-service";

export { useCurrentUser, useIsAuthenticated, AUTH_QUERY_KEYS } from "./queries";

export {
  useRegisterMutation,
  useLoginMutation,
  useLogoutMutation,
  useRefreshTokenMutation,
} from "./mutations";

export type {
  User,
  RegisterRequest,
  LoginRequest,
  LoginResponse,
  TokenResponse,
  MessageResponse,
  ApiResponse,
  ApiError,
} from "@/types/auth.types";
