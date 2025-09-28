import { StrictMode } from "react";
import { RouterProvider } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";

// Styles
import "./styles/index.css";

// Configuration
import { queryClient } from "@/lib/query-client";
import { router } from "./routes";

function App() {
  return (
    <StrictMode>
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    </StrictMode>
  );
}

export default App;
