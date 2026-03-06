import { Navigate, Route, Routes } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/Login";
import { DashboardPage } from "./pages/Dashboard";
import UserManagement from "./pages/UserManagement";
import Chat from "./pages/Chat";
import { isAuthenticated, isAdmin } from "./utils/auth";

function ProtectedRoute({ children }) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

function AdminRoute({ children }) {
  if (!isAuthenticated() || !isAdmin()) {
    return <Navigate to="/chat" replace />;
  }
  return children;
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />

      <Route
        path="/chat"
        element={
          <ProtectedRoute>
            <Chat />
          </ProtectedRoute>
        }
      />

      <Route
        path="/dashboard"
        element={
          <AdminRoute>
            <DashboardPage />
          </AdminRoute>
        }
      />

      <Route
        path="/admin/users"
        element={
          <AdminRoute>
            <UserManagement />
          </AdminRoute>
        }
      />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;