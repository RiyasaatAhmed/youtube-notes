/**
 * Notes Service
 *
 * Handles all notes-related API calls
 */

import apiService from "@/services/api-service";
import { API_ENDPOINTS } from "@/constants/api";
import type {
  Note,
  NoteCreate,
  NoteUpdate,
  NotePagination,
  MessageResponse,
} from "@/types/notes.types";

export class NotesService {
  /**
   * Get all notes with pagination
   * @param params - Query parameters (page, page_size, search)
   * @returns Paginated notes response
   */
  static async getNotes(params?: {
    current_page?: number;
    page_size?: number;
    search?: string;
  }): Promise<NotePagination> {
    const queryParams = new URLSearchParams();
    if (params?.current_page) {
      queryParams.append("current_page", params.current_page.toString());
    }
    if (params?.page_size) {
      queryParams.append("page_size", params.page_size.toString());
    }
    if (params?.search) {
      queryParams.append("search", params.search);
    }

    const queryString = queryParams.toString();
    const url = queryString
      ? `${API_ENDPOINTS.NOTES.GET_ALL}?${queryString}`
      : API_ENDPOINTS.NOTES.GET_ALL;

    return apiService.get<NotePagination>(url);
  }

  /**
   * Get note by ID
   * @param id - Note ID
   * @returns Note data
   */
  static async getNoteById(id: number): Promise<Note> {
    return apiService.get<Note>(API_ENDPOINTS.NOTES.BY_ID(id));
  }

  /**
   * Create a new note
   * @param noteData - Note creation data
   * @returns Created note
   */
  static async createNote(noteData: NoteCreate): Promise<Note> {
    return apiService.post<Note>(API_ENDPOINTS.NOTES.CREATE, noteData);
  }

  /**
   * Update note
   * @param id - Note ID
   * @param noteData - Note update data
   * @returns Updated note
   */
  static async updateNote(
    id: number,
    noteData: NoteUpdate
  ): Promise<Note> {
    return apiService.put<Note>(API_ENDPOINTS.NOTES.UPDATE(id), noteData);
  }

  /**
   * Delete note
   * @param id - Note ID
   * @returns Success message
   */
  static async deleteNote(id: number): Promise<MessageResponse> {
    return apiService.delete<MessageResponse>(API_ENDPOINTS.NOTES.DELETE(id));
  }
}

export default NotesService;

