import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";

export function Header() {
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
          <Link to="/log-in">
            <Button variant="ghost" size="sm">
              Log In
            </Button>
          </Link>
          <Link to="/sign-up">
            <Button size="sm">Sign Up</Button>
          </Link>
        </nav>
      </div>
    </header>
  );
}
