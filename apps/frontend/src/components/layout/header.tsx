import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";

export function Header() {
  const { user, isAuthenticated, isLoading, logout, logoutLoading } = useAuth();

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="m-auto container flex h-16 items-center justify-between">
        <Link to="/" className="flex items-center gap-3">
          <img
            src="/logo.png"
            alt="YouTube Notes Logo"
            className="h-8 w-8 rounded-md"
          />
          <div className="flex flex-col leading-tight text-left">
            <h1 className="text-xl font-semibold text-foreground tracking-tight">
              YouTube Notes
            </h1>
            <span className="text-sm text-muted-foreground">
              Summarize, save, and search YouTube video notes
            </span>
          </div>
        </Link>

        <nav className="flex items-center gap-3">
          {isLoading ? (
            // Show skeleton loaders while checking authentication
            <>
              <div className="h-9 w-20 bg-gray-200 rounded animate-pulse" />
              <div className="h-9 w-20 bg-gray-200 rounded animate-pulse" />
            </>
          ) : isAuthenticated && user ? (
            // Show user menu for authenticated users
            <>
              <span className="text-sm text-muted-foreground">
                {user.first_name} {user.last_name}
              </span>
              <Link to="/notes">
                <Button variant="ghost" size="sm">
                  My Notes
                </Button>
              </Link>
              <Button
                variant="outline"
                size="sm"
                onClick={logout}
                disabled={logoutLoading}
              >
                {logoutLoading ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-black mr-2"></div>
                    Logging out...
                  </div>
                ) : (
                  "Log Out"
                )}
              </Button>
            </>
          ) : (
            // Show login/signup for guests
            <>
              <Link to="/log-in">
                <Button variant="ghost" size="sm">
                  Log In
                </Button>
              </Link>
              <Link to="/sign-up">
                <Button size="sm">Sign Up</Button>
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
