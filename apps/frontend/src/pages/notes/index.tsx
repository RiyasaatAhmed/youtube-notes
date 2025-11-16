/**
 * Notes List Page
 *
 * Displays a paginated list of user's notes with search functionality
 */

import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useNotes, useDeleteNoteMutation } from "@/api/notes";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Search,
  Trash2,
  Eye,
  Calendar,
  User,
  Loader2,
  FileText,
  AlertCircle,
  Play,
  ThumbsUp,
} from "lucide-react";
import type { Note } from "@/types/notes.types";

/**
 * Notes list page component
 *
 * @returns notes list page
 */
export function NotesListPage() {
  const navigate = useNavigate();
  const [currentPage, setCurrentPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const pageSize = 10;

  // Debounce search query
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
      setCurrentPage(1); // Reset to first page on new search
    }, 500);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  const { data, isLoading, error } = useNotes({
    current_page: currentPage,
    page_size: pageSize,
    search: debouncedSearch || undefined,
  });

  const deleteMutation = useDeleteNoteMutation({
    onSuccess: () => {
      // Note list will automatically refetch due to query invalidation
    },
  });

  const handleDelete = async (noteId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (
      window.confirm(
        "Are you sure you want to delete this note? This action cannot be undone."
      )
    ) {
      try {
        await deleteMutation.mutateAsync(noteId);
      } catch (error) {
        console.error("Failed to delete note:", error);
      }
    }
  };

  const handleNoteClick = (noteId: number) => {
    navigate(`/notes/${noteId}`);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const truncateText = (text: string | null, maxLength: number = 150) => {
    if (!text) return "No summary available";
    if (text.length <= maxLength) return text;
    return `${text.substring(0, maxLength)}...`;
  };

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return null;
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, "0")}:${secs
        .toString()
        .padStart(2, "0")}`;
    }
    return `${minutes}:${secs.toString().padStart(2, "0")}`;
  };

  const formatNumber = (num: number | null) => {
    if (!num) return null;
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M`;
    }
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K`;
    }
    return num.toString();
  };

  return (
    <div className="container mx-auto max-w-7xl">
      {/* Search Bar */}
      <div className="mb-6">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
          <Input
            type="search"
            placeholder="Search notes by title, channel, or content..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
            aria-label="Search notes"
          />
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
          <span className="sr-only">Loading notes...</span>
        </div>
      )}

      {/* Error State */}
      {error && (
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-destructive">
              <AlertCircle className="w-5 h-5" />
              <p>
                Failed to load notes. Please try again later.
                {error instanceof Error && ` ${error.message}`}
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {!isLoading && !error && data && data.notes.length === 0 && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <FileText className="w-12 h-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No notes found</h3>
              <p className="text-muted-foreground mb-4">
                {debouncedSearch
                  ? "No notes match your search criteria."
                  : "You haven't created any notes yet. Start by creating a note from a YouTube video."}
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Notes Grid */}
      {!isLoading && !error && data && data.notes.length > 0 && (
        <>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 mb-6">
            {data.notes.map((note: Note) => (
              <Card
                key={note.id}
                className="cursor-pointer hover:shadow-lg transition-shadow focus-within:ring-2 focus-within:ring-ring overflow-hidden"
                onClick={() => handleNoteClick(note.id)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    handleNoteClick(note.id);
                  }
                }}
                tabIndex={0}
                role="button"
                aria-label={`View note: ${note.video_title || "Untitled"}`}
              >
                {/* Thumbnail */}
                {note.thumbnail_url && (
                  <div className="relative w-full h-48 overflow-hidden bg-muted">
                    <img
                      src={note.thumbnail_url}
                      alt={note.video_title || "Video thumbnail"}
                      className="w-full h-full object-cover"
                      loading="lazy"
                    />
                    {note.duration_in_seconds && (
                      <div className="absolute bottom-2 right-2 bg-black/75 text-white text-xs px-2 py-1 rounded flex items-center gap-1">
                        <Play className="w-3 h-3" />
                        {formatDuration(note.duration_in_seconds)}
                      </div>
                    )}
                  </div>
                )}

                <CardHeader>
                  <div className="flex items-start justify-between gap-2">
                    <CardTitle className="text-lg line-clamp-2 flex-1">
                      {note.video_title || "Untitled Video"}
                    </CardTitle>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 shrink-0"
                      onClick={(e) => handleDelete(note.id, e)}
                      aria-label={`Delete note: ${
                        note.video_title || "Untitled"
                      }`}
                    >
                      <Trash2 className="w-4 h-4 text-destructive" />
                    </Button>
                  </div>
                  {note.channel_name && (
                    <CardDescription className="flex items-center gap-1">
                      <User className="w-3 h-3" />
                      {note.channel_name}
                    </CardDescription>
                  )}
                  {/* Video Stats */}
                  {(note.views !== null || note.likes !== null) && (
                    <div className="flex items-center gap-3 text-xs text-muted-foreground pt-1">
                      {note.views !== null && (
                        <div className="flex items-center gap-1">
                          <Eye className="w-3 h-3" />
                          {formatNumber(note.views)}
                        </div>
                      )}
                      {note.likes !== null && (
                        <div className="flex items-center gap-1">
                          <ThumbsUp className="w-3 h-3" />
                          {formatNumber(note.likes)}
                        </div>
                      )}
                    </div>
                  )}
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground line-clamp-3">
                    {truncateText(note.summary)}
                  </p>
                  {note.key_points && note.key_points.length > 0 && (
                    <div className="mt-3">
                      <p className="text-xs text-muted-foreground">
                        {note.key_points.length} key point
                        {note.key_points.length !== 1 ? "s" : ""}
                      </p>
                    </div>
                  )}
                </CardContent>
                <CardFooter className="flex items-center justify-between text-xs text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    {formatDate(note.created_at)}
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleNoteClick(note.id);
                    }}
                  >
                    <Eye className="w-3 h-3 mr-1" />
                    View
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>

          {/* Pagination */}
          {data.total_pages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Showing {data.notes.length} of {data.total_notes} notes
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    setCurrentPage((prev) => Math.max(1, prev - 1))
                  }
                  disabled={currentPage === 1 || isLoading}
                  aria-label="Previous page"
                >
                  Previous
                </Button>
                <span className="text-sm text-muted-foreground">
                  Page {data.current_page} of {data.total_pages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    setCurrentPage((prev) =>
                      Math.min(data.total_pages, prev + 1)
                    )
                  }
                  disabled={currentPage === data.total_pages || isLoading}
                  aria-label="Next page"
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
