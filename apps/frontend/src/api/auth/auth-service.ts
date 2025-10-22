/**
 * Authentication Service
 *
 * Handles all authentication-related API calls
 */

import apiService from "@/services/api-service";
import { API_ENDPOINTS } from "@/constants/api";
import type {
  User,
  RegisterRequest,
  LoginRequest,
  LoginResponse,
  TokenResponse,
  MessageResponse,
} from "@/types/auth.types";

export class AuthService {
  /**
   * Register a new user
   * @param userData - User registration data
   * @returns Created user data
   */
  static async register(userData: RegisterRequest): Promise<User> {
    return apiService.post<User>(API_ENDPOINTS.AUTH.REGISTER, userData);
  }

  /**
   * Login user
   * @param credentials - Email and password
   * @returns Login response with token and user data
   */
  static async login(credentials: LoginRequest): Promise<LoginResponse> {
    return apiService.post<LoginResponse>(
      API_ENDPOINTS.AUTH.LOGIN,
      credentials
    );
  }

  /**
   * Logout current user
   * @returns Success message
   */
  static async logout(): Promise<MessageResponse> {
    return apiService.post<MessageResponse>(API_ENDPOINTS.AUTH.LOGOUT);
  }

  /**
   * Get current authenticated user
   * @returns Current user data
   */
  static async getCurrentUser(): Promise<User> {
    return apiService.get<User>(API_ENDPOINTS.AUTH.ME);
  }

  /**
   * Refresh access token
   * @returns New tokens and user data
   */
  static async refreshToken(): Promise<TokenResponse> {
    return apiService.post<TokenResponse>(API_ENDPOINTS.AUTH.REFRESH);
  }

  /**
   * Check if user is authenticated
   * @returns Boolean indicating authentication status
   */
  static async isAuthenticated(): Promise<boolean> {
    try {
      await this.getCurrentUser();
      return true;
    } catch {
      return false;
    }
  }
}

export default AuthService;
