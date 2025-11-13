/**
 * Note Detail Page
 *
 * Displays detailed information about a specific note
 */

import { useParams, useNavigate } from "react-router-dom";
import { useNote, useDeleteNoteMutation } from "@/api/notes";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  ArrowLeft,
  Calendar,
  User,
  Loader2,
  AlertCircle,
  Trash2,
  ExternalLink,
  Clock,
  List,
} from "lucide-react";
import type { Timestamp } from "@/types/notes.types";

/**
 * Note detail page component
 *
 * @returns note detail page
 */
export function NoteDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const noteId = id ? parseInt(id, 10) : 0;

  const { data: note, isLoading, error } = useNote(noteId);

  const deleteMutation = useDeleteNoteMutation({
    onSuccess: () => {
      navigate("/notes");
    },
  });

  const handleDelete = async () => {
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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const openYouTubeVideo = (url: string) => {
    window.open(url, "_blank", "noopener,noreferrer");
  };

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
          <span className="sr-only">Loading note...</span>
        </div>
      </div>
    );
  }

  if (error || !note) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <Button
          variant="ghost"
          onClick={() => navigate("/notes")}
          className="mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Notes
        </Button>
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-destructive">
              <AlertCircle className="w-5 h-5" />
              <p>
                Failed to load note. Please try again later.
                {error instanceof Error && ` ${error.message}`}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      {/* Back Button */}
      <Button
        variant="ghost"
        onClick={() => navigate("/notes")}
        className="mb-6"
        aria-label="Back to notes list"
      >
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back to Notes
      </Button>

      {/* Main Content */}
      <div className="space-y-6">
        {/* Header Card */}
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <CardTitle className="text-2xl mb-2">
                  {note.video_title || "Untitled Video"}
                </CardTitle>
                {note.channel_name && (
                  <CardDescription className="flex items-center gap-2 text-base">
                    <User className="w-4 h-4" />
                    {note.channel_name}
                  </CardDescription>
                )}
              </div>
              <div className="flex gap-2 shrink-0">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => openYouTubeVideo(note.youtube_url)}
                  aria-label="Open video on YouTube"
                >
                  <ExternalLink className="w-4 h-4 mr-2" />
                  Watch Video
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={handleDelete}
                  disabled={deleteMutation.isPending}
                  aria-label="Delete note"
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  {deleteMutation.isPending ? "Deleting..." : "Delete"}
                </Button>
              </div>
            </div>
            <div className="flex items-center gap-4 text-sm text-muted-foreground mt-4">
              <div className="flex items-center gap-1">
                <Calendar className="w-4 h-4" />
                Created: {formatDate(note.created_at)}
              </div>
              {note.updated_at !== note.created_at && (
                <div className="flex items-center gap-1">
                  <Calendar className="w-4 h-4" />
                  Updated: {formatDate(note.updated_at)}
                </div>
              )}
            </div>
          </CardHeader>
        </Card>

        {/* Summary Card */}
        {note.summary && (
          <Card>
            <CardHeader>
              <CardTitle className="text-xl">Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-base leading-relaxed whitespace-pre-wrap">
                {note.summary}
              </p>
            </CardContent>
          </Card>
        )}

        {/* Key Points Card */}
        {note.key_points && note.key_points.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-xl flex items-center gap-2">
                <List className="w-5 h-5" />
                Key Points
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3">
                {note.key_points.map((point, index) => (
                  <li
                    key={index}
                    className="flex gap-3 text-base leading-relaxed"
                  >
                    <span className="text-primary font-semibold shrink-0">
                      {index + 1}.
                    </span>
                    <span className="flex-1">{point}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {/* Timestamps Card */}
        {note.timestamps && note.timestamps.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-xl flex items-center gap-2">
                <Clock className="w-5 h-5" />
                Important Timestamps
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {note.timestamps.map((timestamp: Timestamp, index: number) => (
                  <div
                    key={index}
                    className="flex gap-4 p-4 rounded-lg border bg-card"
                  >
                    <div className="shrink-0">
                      <div className="flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 text-primary font-mono font-semibold">
                        {timestamp.time}
                      </div>
                    </div>
                    <div className="flex-1 pt-1">
                      <p className="text-base leading-relaxed">
                        {timestamp.description}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Empty State for missing content */}
        {!note.summary &&
          (!note.key_points || note.key_points.length === 0) &&
          (!note.timestamps || note.timestamps.length === 0) && (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-8 text-muted-foreground">
                  <p>This note doesn't have any content yet.</p>
                </div>
              </CardContent>
            </Card>
          )}
      </div>
    </div>
  );
}

