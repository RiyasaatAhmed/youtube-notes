import { QueryClient } from "@tanstack/react-query";
import { secrets } from "@/constants/secrets";

/**
 * Configured React Query client with default options.
 * Provides caching and data fetching capabilities for the application.
 *
 * @constant {QueryClient} queryClient - The configured query client instance
 */
export const queryClient: QueryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Time in milliseconds after which data is considered stale
      staleTime: secrets.TANSTACK_STALE_TIME,
      // Time in milliseconds after which unused data is garbage collected
      gcTime: secrets.TANSTACK_GARBAGE_COLLECTION_TIME,
    },
  },
});
