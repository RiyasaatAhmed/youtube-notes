import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ArrowUp } from "lucide-react";
import { useState } from "react";

/**
 * Home page component.
 *
 * @returns home page
 */
export function HomePage() {
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      // Handle YouTube URL processing logic here
      console.log("Processing YouTube URL:", youtubeUrl);

      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 2000));

      // Redirect to notes page or show results
      // navigate("/notes");
    } catch (error) {
      console.error("Failed to process YouTube URL:", error);
    } finally {
      setIsLoading(false);
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
                disabled={isLoading || !isValidYouTubeUrl(youtubeUrl)}
              >
                <ArrowUp className="w-4 h-4 stroke-4" />
              </Button>
            </div>
            {youtubeUrl && !isValidYouTubeUrl(youtubeUrl) && (
              <p className="text-sm text-red-600">
                Please enter a valid YouTube URL
              </p>
            )}
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
