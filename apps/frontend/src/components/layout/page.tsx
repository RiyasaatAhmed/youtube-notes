import { cn } from "@/lib/utils";
import type { PropsWithChildren } from "react";

interface PageProps extends PropsWithChildren {
  className?: string;
}

export function Page({ children, className }: PageProps) {
  return (
    <main
      className={cn(
        "py-8 min-h-[calc(100vh-65px)] container mx-auto",
        className
      )}
    >
      {children}
    </main>
  );
}
