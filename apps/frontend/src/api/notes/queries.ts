/**
 * Notes Queries
 *
 * React Query hooks for fetching notes data
 */

import { useQuery, type UseQueryOptions } from "@tanstack/react-query";
import NotesService from "./notes-service";
import type { Note, NotePagination } from "@/types/notes.types";

/**
 * Query keys for notes
 */
export const NOTES_QUERY_KEYS = {
  all: ["notes"] as const,
  lists: () => [...NOTES_QUERY_KEYS.all, "list"] as const,
  list: (params?: {
    current_page?: number;
    page_size?: number;
    search?: string;
  }) => [...NOTES_QUERY_KEYS.lists(), params] as const,
  details: () => [...NOTES_QUERY_KEYS.all, "detail"] as const,
  detail: (id: number) => [...NOTES_QUERY_KEYS.details(), id] as const,
} as const;

/**
 * Hook to get all notes with pagination
 *
 * @example
 * ```tsx
 * const { data, isLoading, error } = useNotes({ current_page: 1, page_size: 10 })
 * ```
 */
export const useNotes = (
  params?: {
    current_page?: number;
    page_size?: number;
    search?: string;
  },
  options?: Omit<
    UseQueryOptions<NotePagination, Error>,
    "queryKey" | "queryFn"
  >
) => {
  return useQuery<NotePagination, Error>({
    queryKey: NOTES_QUERY_KEYS.list(params),
    queryFn: () => NotesService.getNotes(params),
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  });
};

/**
 * Hook to get note by ID
 *
 * @example
 * ```tsx
 * const { data: note, isLoading, error } = useNote(1)
 * ```
 */
export const useNote = (
  id: number,
  options?: Omit<UseQueryOptions<Note, Error>, "queryKey" | "queryFn">
) => {
  return useQuery<Note, Error>({
    queryKey: NOTES_QUERY_KEYS.detail(id),
    queryFn: () => NotesService.getNoteById(id),
    enabled: !!id, // Only fetch if id is provided
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    ...options,
  });
};

