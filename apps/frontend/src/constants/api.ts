/**
 * API Endpoints Constants
 *
 * Centralized API endpoint definitions
 */

import { secrets } from "@/constants/secrets";

const BASE_URL = secrets.BACKEND_URL;

export const API_ENDPOINTS = {
  AUTH: {
    REGISTER: "/api/users/register",
    LOGIN: "/api/users/login",
    LOGOUT: "/api/users/logout",
    ME: "/api/users/me",
    REFRESH: "/api/users/refresh",
  },
  USERS: {
    GET_ALL: "/api/users/",
    BY_ID: (id: number) => `/api/users/${id}`,
    UPDATE: (id: number) => `/api/users/${id}`,
    DELETE: (id: number) => `/api/users/${id}`,
    ACTIVATE: (id: number) => `/api/users/${id}/activate`,
    DEACTIVATE: (id: number) => `/api/users/${id}/deactivate`,
    VERIFY: (id: number) => `/api/users/${id}/verify`,
  },
  NOTES: {
    GET_ALL: "/api/notes/",
    BY_ID: (id: number) => `/api/notes/${id}`,
    CREATE: "/api/notes/",
    UPDATE: (id: number) => `/api/notes/${id}`,
    DELETE: (id: number) => `/api/notes/${id}`,
  },
} as const;

export { BASE_URL };
