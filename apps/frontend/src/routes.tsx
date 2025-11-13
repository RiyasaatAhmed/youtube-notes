import { createBrowserRouter } from "react-router-dom";
import type { RouteObject } from "react-router-dom";
import { Layout } from "@/components/layout";

// Pages
import { LoginPage } from "@/pages/login";
import { SignUpPage } from "@/pages/sign-up";
import { ForgetPasswordPage } from "@/pages/forget-password";
import { HomePage } from "@/pages/home";
import { NotesListPage } from "@/pages/notes";
import { NoteDetailPage } from "@/pages/notes/detail";

/** Route definitions */
const routes: Array<RouteObject> = [
  {
    path: "/",
    element: <Layout />,
    children: [
      {
        index: true,
        element: <HomePage />,
      },
      {
        path: "notes",
        element: <NotesListPage />,
      },
      {
        path: "notes/:id",
        element: <NoteDetailPage />,
      },
    ],
  },
  {
    path: "/log-in",
    element: <LoginPage />,
  },
  {
    path: "/sign-up",
    element: <SignUpPage />,
  },
  {
    path: "/forgot-password",
    element: <ForgetPasswordPage />,
  },
];

/** Export configured router */
export const router = createBrowserRouter(routes);
