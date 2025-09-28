import { Page } from "@/components/layout/page";
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
import { Label } from "@/components/ui/label";
import { useState } from "react";
import { Link } from "react-router-dom";

/**
 * Forget password page component.
 *
 * @returns forget password page
 */
export function ForgetPasswordPage() {
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isEmailSent, setIsEmailSent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      // Handle password reset logic here
      console.log("Password reset request for:", email);

      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1000));

      setIsEmailSent(true);
    } catch (error) {
      console.error("Password reset failed:", error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isEmailSent) {
    return (
      <Page className="flex items-center justify-center h-screen">
        <Card className="w-full max-w-sm">
          <CardHeader className="text-center">
            <CardTitle>Check your email</CardTitle>
            <CardDescription>
              We've sent a password reset link to your email address
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center">
            <div className="mb-4">
              <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
                <svg
                  className="w-8 h-8 text-green-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
              <p className="text-sm text-gray-600">
                If you don't see the email, check your spam folder or try again.
              </p>
            </div>
          </CardContent>
          <CardFooter className="flex-col gap-2">
            <Button
              className="w-full"
              onClick={() => {
                setIsEmailSent(false);
                setEmail("");
              }}
            >
              Send another email
            </Button>
            <Link className="w-full" to="/log-in">
              <Button variant="outline" className="w-full hover:underline!">
                Back to Sign In
              </Button>
            </Link>
          </CardFooter>
        </Card>
      </Page>
    );
  }

  return (
    <Page className="flex items-center justify-center h-screen">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Forgot your password?</CardTitle>
          <CardDescription>
            Enter your email address and we'll send you a link to reset your
            password
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit}>
            <div className="flex flex-col gap-6">
              <div className="grid gap-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="m@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            </div>
          </form>
        </CardContent>
        <CardFooter className="flex-col gap-2">
          <Button
            type="submit"
            className="w-full"
            disabled={isLoading}
            onClick={handleSubmit}
          >
            {isLoading ? (
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Sending reset link...
              </div>
            ) : (
              "Send reset link"
            )}
          </Button>
          <Link className="w-full" to="/log-in">
            <Button variant="outline" className="w-full hover:underline">
              Back to Sign In
            </Button>
          </Link>
        </CardFooter>
      </Card>
    </Page>
  );
}
