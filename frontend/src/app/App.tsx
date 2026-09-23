import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { lazy } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router";
import { LandingPage } from "@/features/landing/LandingPage";
import { ApiError } from "@/lib/api";
import { AppShell } from "./AppShell";

const ChatPage = lazy(() =>
  import("@/features/chat/ChatPage").then((module) => ({ default: module.ChatPage })),
);
const DocumentsPage = lazy(() =>
  import("@/features/documents/DocumentsPage").then((module) => ({
    default: module.DocumentsPage,
  })),
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
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route element={<AppShell />}>
            <Route path="/chat/:sessionId?" element={<ChatPage />} />
            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/search" element={<SearchInspectorPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
