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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  ArrowLeft,
  Calendar,
  User,
  Loader2,
  AlertCircle,
  Trash2,
  Clock,
  List,
  Eye,
  ThumbsUp,
  Play,
  MoreHorizontal,
  Pencil,
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

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return "N/A";
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
    if (!num) return "N/A";
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M`;
    }
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K`;
    }
    return num.toString();
  };

  const openYouTubeVideo = (url: string) => {
    window.open(url, "_blank", "noopener,noreferrer");
  };

  const openYouTubeVideoAtTimestamp = (url: string, timestamp: string) => {
    // Extract video ID from YouTube URL
    const videoIdMatch = url.match(
      /(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})/
    );
    if (!videoIdMatch) {
      // Fallback to original URL if we can't extract video ID
      openYouTubeVideo(url);
      return;
    }

    const videoId = videoIdMatch[1];

    // Convert timestamp (MM:SS or HH:MM:SS) to seconds
    const timeParts = timestamp.split(":").map(Number);
    let totalSeconds = 0;

    if (timeParts.length === 2) {
      // MM:SS format
      totalSeconds = timeParts[0] * 60 + timeParts[1];
    } else if (timeParts.length === 3) {
      // HH:MM:SS format
      totalSeconds = timeParts[0] * 3600 + timeParts[1] * 60 + timeParts[2];
    }

    // Create YouTube URL with timestamp
    const timestampUrl = `https://www.youtube.com/watch?v=${videoId}&t=${totalSeconds}s`;
    window.open(timestampUrl, "_blank", "noopener,noreferrer");
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
    <div className="container mx-auto max-w-4xl">
      {/* Main Content */}
      <div className="space-y-6">
        {/* Header Card with Thumbnail */}
        <Card>
          <CardHeader>
            <div className="flex flex-col md:flex-row gap-6">
              {/* Thumbnail */}
              {note.thumbnail_url && (
                <div className="shrink-0">
                  <img
                    src={note.thumbnail_url}
                    alt={note.video_title || "Video thumbnail"}
                    className="w-full md:w-64 h-auto rounded-lg object-cover"
                    loading="lazy"
                  />
                </div>
              )}

              {/* Content */}
              <div className="flex-1 space-y-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <CardTitle className="text-2xl mb-2">
                      <span
                        role="link"
                        className="cursor-pointer hover:underline"
                        onClick={() => openYouTubeVideo(note.youtube_url)}
                      >
                        {note.video_title || "Untitled Video"}
                      </span>
                    </CardTitle>
                    {note.channel_name && (
                      <CardDescription className="flex items-center gap-2 text-base">
                        <User className="w-4 h-4" />
                        {note.channel_name}
                      </CardDescription>
                    )}
                  </div>

                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 w-8 p-0"
                        aria-label="More options"
                      >
                        <MoreHorizontal className="h-4 w-4" />
                        <span className="sr-only">Open menu</span>
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem
                        onClick={() => {
                          // TODO: Implement edit functionality
                          console.log("Edit note");
                        }}
                        className="cursor-pointer"
                      >
                        <Pencil className="mr-2 h-4 w-4" />
                        <span>Edit</span>
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={handleDelete}
                        disabled={deleteMutation.isPending}
                        className="cursor-pointer text-destructive focus:text-destructive"
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        <span>
                          {deleteMutation.isPending ? "Deleting..." : "Delete"}
                        </span>
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>

                {/* Video Stats */}
                <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
                  {note.duration_in_seconds && (
                    <div className="flex items-center gap-1">
                      <Play className="w-4 h-4" />
                      <span>{formatDuration(note.duration_in_seconds)}</span>
                    </div>
                  )}
                  {note.views !== null && (
                    <div className="flex items-center gap-1">
                      <Eye className="w-4 h-4" />
                      <span>{formatNumber(note.views)} views</span>
                    </div>
                  )}
                  {note.likes !== null && (
                    <div className="flex items-center gap-1">
                      <ThumbsUp className="w-4 h-4" />
                      <span>{formatNumber(note.likes)} likes</span>
                    </div>
                  )}
                  {note.publish_date && (
                    <div className="flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      <span>Published: {formatDate(note.publish_date)}</span>
                    </div>
                  )}
                </div>
              </div>
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
                      <button
                        onClick={() =>
                          openYouTubeVideoAtTimestamp(
                            note.youtube_url,
                            timestamp.time
                          )
                        }
                        className="text-blue-500 hover:text-blue-600 hover:underline font-mono font-semibold text-base transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 rounded px-2 py-1"
                        aria-label={`Jump to ${timestamp.time} in video`}
                      >
                        {timestamp.time}
                      </button>
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
