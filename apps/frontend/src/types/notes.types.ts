/**
 * Notes Types
 *
 * Type definitions for notes-related data structures
 */

export interface Note {
  id: number;
  user_id: number;
  youtube_url: string;
  video_title: string | null;
  channel_name: string | null;
  summary: string | null;
  key_points: string[] | null;
  timestamps: Timestamp[] | null;
  duration_in_seconds: number | null;
  thumbnail_url: string | null;
  views: number | null;
  likes: number | null;
  publish_date: string | null;
  created_at: string;
  updated_at: string;
}

export interface Timestamp {
  time: string;
  description: string;
}

export interface NoteCreate {
  youtube_url: string;
}

export interface NoteUpdate {
  video_title?: string;
  channel_name?: string;
  summary?: string;
  key_points?: string[];
  timestamps?: Timestamp[];
  duration_in_seconds?: number;
  thumbnail_url?: string;
  views?: number;
  likes?: number;
  publish_date?: string;
}

export interface NotePagination {
  notes: Note[];
  total_notes: number;
  total_pages: number;
  current_page: number;
  page_size: number;
}

export interface MessageResponse {
  message: string;
}
