import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ArrowUp, Loader2, AlertCircle } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCreateNoteMutation } from "@/api/notes";

/**
 * Home page component.
 *
 * @returns home page
 */
export function HomePage() {
  const navigate = useNavigate();
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [error, setError] = useState<string | null>(null);

  const createNoteMutation = useCreateNoteMutation({
    onSuccess: (note) => {
      // Navigate to the created note detail page
      navigate(`/notes/${note.id}`);
    },
    onError: (error) => {
      setError(
        error instanceof Error
          ? error.message
          : "Failed to create note. Please try again."
      );
    },
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!isValidYouTubeUrl(youtubeUrl)) {
      setError("Please enter a valid YouTube URL");
      return;
    }

    try {
      await createNoteMutation.mutateAsync({ youtube_url: youtubeUrl });
    } catch (error) {
      // Error is handled in onError callback
      console.error("Failed to create note:", error);
    }
  };

  const isValidYouTubeUrl = (url: string) => {
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+/;
    return youtubeRegex.test(url);
  };

  return (
    <div className="flex h-[calc(100vh-130px)] items-center justify-center">
      <Card className="w-full border-none! shadow-none! max-w-3xl">
        <CardContent>
          <form onSubmit={handleSubmit} className="h-16 flex flex-col gap-2">
            <div className="flex gap-6 relative">
              <div className="flex flex-col gap-2 w-full">
                <Input
                  id="youtube-url"
                  name="youtube-url"
                  type="url"
                  placeholder="https://www.youtube.com/watch?v=..."
                  value={youtubeUrl}
                  onChange={(e) => setYoutubeUrl(e.target.value)}
                  required
                  className="text-lg py-3"
                />
              </div>

              <Button
                type="submit"
                className="text-md font-semibold h-8 w-8 p-0 rounded-full absolute right-2 top-1"
                disabled={
                  createNoteMutation.isPending || !isValidYouTubeUrl(youtubeUrl)
                }
                aria-label="Create note from YouTube URL"
              >
                {createNoteMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <ArrowUp className="w-4 h-4 stroke-4" />
                )}
              </Button>
            </div>
            {error && (
              <div className="flex items-center gap-2 text-sm text-destructive">
                <AlertCircle className="w-4 h-4" />
                <p>{error}</p>
              </div>
            )}
            {youtubeUrl && !isValidYouTubeUrl(youtubeUrl) && !error && (
              <p className="text-sm text-destructive">
                Please enter a valid YouTube URL
              </p>
            )}
            {createNoteMutation.isPending && (
              <p className="text-sm text-muted-foreground">
                Creating note from video... This may take a few moments.
              </p>
            )}
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
