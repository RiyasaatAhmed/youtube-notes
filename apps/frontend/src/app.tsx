import { StrictMode } from "react";
import { RouterProvider } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";

// Styles
import "./styles/index.css";

// Configuration
import { queryClient } from "@/lib/query-client";
import { router } from "./routes";

// Providers
import { AuthProvider } from "./providers/auth-provider";

function App() {
  return (
    <StrictMode>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <RouterProvider router={router} />
        </AuthProvider>
      </QueryClientProvider>
    </StrictMode>
  );
}

export default App;
