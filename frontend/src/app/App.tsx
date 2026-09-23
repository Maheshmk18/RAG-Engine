import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { lazy } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router";
import { LoginPage } from "@/features/auth/LoginPage";
import { LandingPage } from "@/features/landing/LandingPage";
import { ApiError } from "@/lib/api";
import { AuthProvider } from "@/lib/auth";
import { AppShell } from "./AppShell";
import { RequireAdmin, RequireAuth } from "./guards";

const ChatPage = lazy(() =>
  import("@/features/chat/ChatPage").then((module) => ({ default: module.ChatPage })),
);
const DocumentsPage = lazy(() =>
  import("@/features/documents/DocumentsPage").then((module) => ({
    default: module.DocumentsPage,
  })),
);
const UsersPage = lazy(() =>
  import("@/features/admin/UsersPage").then((module) => ({ default: module.UsersPage })),
);
const SearchInspectorPage = lazy(() =>
  import("@/features/admin/SearchInspectorPage").then((module) => ({
    default: module.SearchInspectorPage,
  })),
);

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
      retry: (count, error) => !(error instanceof ApiError && error.status < 500) && count < 2,
    },
  },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route element={<RequireAuth />}>
              <Route element={<AppShell />}>
                <Route path="/chat/:sessionId?" element={<ChatPage />} />
                <Route path="/documents" element={<DocumentsPage />} />
                <Route element={<RequireAdmin />}>
                  <Route path="/admin/users" element={<UsersPage />} />
                  <Route path="/admin/search" element={<SearchInspectorPage />} />
                </Route>
              </Route>
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}
