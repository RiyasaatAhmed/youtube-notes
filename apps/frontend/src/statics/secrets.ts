import type { Secret } from "@/types/secret.types";

/** Application secrets and configuration */
export const secrets: Secret = {
  BACKEND_URL: import.meta.env.VITE_PUBLIC_BACKEND_URL,
  TANSTACK_STALE_TIME: import.meta.env.VITE_PUBLIC_TANSTACK_STALE_TIME,
  TANSTACK_GARBAGE_COLLECTION_TIME: import.meta.env
    .VITE_PUBLIC_TANSTACK_GARBAGE_COLLECTION_TIME,
  API_TIMEOUT: import.meta.env.VITE_PUBLIC_API_TIMEOUT,
};
