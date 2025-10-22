/**
 * Authentication Hooks
 *
 * Custom hooks for authentication functionality
 */

import { useContext } from "react";
import { AuthContext, type AuthContextValue } from "@/contexts/auth-context";
import type { User } from "@/api/auth";

/**
 * Hook to use authentication context
 *
 * @throws {Error} If used outside of AuthProvider
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const { user, isAuthenticated, login, logout } = useAuth();
 *
 *   if (isLoading) return <div>Loading...</div>;
 *
 *   return (
 *     <div>
 *       {isAuthenticated ? (
 *         <>
 *           <p>Welcome, {user.first_name}!</p>
 *           <button onClick={logout}>Logout</button>
 *         </>
 *       ) : (
 *         <button onClick={() => login({ email, password })}>Login</button>
 *       )}
 *     </div>
 *   );
 * }
 * ```
 */
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }

  return context;
}

/**
 * Hook to require authentication
 *
 * Throws an error if user is not authenticated
 * Useful for protected components
 *
 * @example
 * ```tsx
 * function ProtectedComponent() {
 *   const user = useRequireAuth();
 *   // user is guaranteed to be non-null here
 *
 *   return <div>Welcome, {user.first_name}!</div>;
 * }
 * ```
 */
export function useRequireAuth(): User {
  const { user, isAuthenticated } = useAuth();

  if (!isAuthenticated || !user) {
    throw new Error("Authentication required");
  }

  return user;
}

/**
 * Hook to get user information (can be null)
 *
 * @example
 * ```tsx
 * function ProfileComponent() {
 *   const user = useUser();
 *
 *   if (!user) {
 *     return <div>Please login</div>;
 *   }
 *
 *   return <div>Welcome, {user.first_name}!</div>;
 * }
 * ```
 */
export function useUser(): User | null {
  const { user } = useAuth();
  return user;
}

/**
 * Hook to check authentication status
 *
 * @example
 * ```tsx
 * function NavigationComponent() {
 *   const isAuthenticated = useIsAuthenticatedStatus();
 *
 *   return (
 *     <nav>
 *       {isAuthenticated ? (
 *         <Link to="/dashboard">Dashboard</Link>
 *       ) : (
 *         <Link to="/login">Login</Link>
 *       )}
 *     </nav>
 *   );
 * }
 * ```
 */
export function useIsAuthenticatedStatus(): boolean {
  const { isAuthenticated } = useAuth();
  return isAuthenticated;
}
