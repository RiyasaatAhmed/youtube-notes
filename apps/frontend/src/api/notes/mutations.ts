/**
 * Notes Mutations
 *
 * React Query hooks for notes mutations
 */

import {
  useMutation,
  useQueryClient,
  type UseMutationOptions,
} from "@tanstack/react-query";
import NotesService from "./notes-service";
import { NOTES_QUERY_KEYS } from "./queries";
import type {
  Note,
  NoteCreate,
  NoteUpdate,
  MessageResponse,
} from "@/types/notes.types";

/**
 * Hook for creating a new note
 *
 * @example
 * ```tsx
 * const createMutation = useCreateNoteMutation()
 *
 * const handleCreate = async (data: NoteCreate) => {
 *   try {
 *     const note = await createMutation.mutateAsync(data)
 *     console.log('Created:', note)
 *   } catch (error) {
 *     console.error('Creation failed:', error)
 *   }
 * }
 * ```
 */
export const useCreateNoteMutation = (
  options?: Omit<UseMutationOptions<Note, Error, NoteCreate>, "mutationFn">
) => {
  const queryClient = useQueryClient();

  return useMutation<Note, Error, NoteCreate>({
    mutationFn: NotesService.createNote,
    onSuccess: () => {
      // Invalidate notes list to refetch
      queryClient.invalidateQueries({
        queryKey: NOTES_QUERY_KEYS.lists(),
      });
    },
    ...options,
  });
};

/**
 * Hook for updating a note
 *
 * @example
 * ```tsx
 * const updateMutation = useUpdateNoteMutation()
 *
 * const handleUpdate = async (id: number, data: NoteUpdate) => {
 *   try {
 *     const note = await updateMutation.mutateAsync({ id, data })
 *     console.log('Updated:', note)
 *   } catch (error) {
 *     console.error('Update failed:', error)
 *   }
 * }
 * ```
 */
export const useUpdateNoteMutation = (
  options?: Omit<
    UseMutationOptions<Note, Error, { id: number; data: NoteUpdate }>,
    "mutationFn"
  >
) => {
  const queryClient = useQueryClient();

  return useMutation<Note, Error, { id: number; data: NoteUpdate }>({
    mutationFn: ({ id, data }) => NotesService.updateNote(id, data),
    onSuccess: (updatedNote) => {
      // Update the specific note in cache
      queryClient.setQueryData(
        NOTES_QUERY_KEYS.detail(updatedNote.id),
        updatedNote
      );
      // Invalidate notes list to refetch
      queryClient.invalidateQueries({
        queryKey: NOTES_QUERY_KEYS.lists(),
      });
    },
    ...options,
  });
};

/**
 * Hook for deleting a note
 *
 * @example
 * ```tsx
 * const deleteMutation = useDeleteNoteMutation()
 *
 * const handleDelete = async (id: number) => {
 *   try {
 *     await deleteMutation.mutateAsync(id)
 *     console.log('Deleted successfully')
 *   } catch (error) {
 *     console.error('Delete failed:', error)
 *   }
 * }
 * ```
 */
export const useDeleteNoteMutation = (
  options?: Omit<UseMutationOptions<MessageResponse, Error, number>, "mutationFn">
) => {
  const queryClient = useQueryClient();

  return useMutation<MessageResponse, Error, number>({
    mutationFn: NotesService.deleteNote,
    onSuccess: (_, deletedId) => {
      // Remove the note from cache
      queryClient.removeQueries({
        queryKey: NOTES_QUERY_KEYS.detail(deletedId),
      });
      // Invalidate notes list to refetch
      queryClient.invalidateQueries({
        queryKey: NOTES_QUERY_KEYS.lists(),
      });
    },
    ...options,
  });
};

