/** Environment configuration interface */
export interface Secret {
  BACKEND_URL: string;
  TANSTACK_STALE_TIME: number;
  TANSTACK_GARBAGE_COLLECTION_TIME: number;
  API_TIMEOUT: number;
}
