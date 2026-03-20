import { Navigate, Route, Routes } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/Login";
import { DashboardPage } from "./pages/Dashboard";
import UserManagement from "./pages/UserManagement";
import Chat from "./pages/Chat";
import AdminDashboard from "./pages/AdminDashboard";
import HRDashboard from "./pages/HRDashboard";
import ManagerDashboard from "./pages/ManagerDashboard";
import EmployeeDashboard from "./pages/EmployeeDashboard";
import { isAuthenticated, isAdmin, getUser } from "./utils/auth";

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

function RoleRoute({ children, allowedRoles }) {
  const user = getUser();
  if (!isAuthenticated() || !user) {
    return <Navigate to="/login" replace />;
  }
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/chat" replace />;
  }
  return children;
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />

      {/* Role-specific dashboards */}
      <Route
        path="/admin-dashboard"
        element={
          <RoleRoute allowedRoles={["admin"]}>
            <AdminDashboard />
          </RoleRoute>
        }
      />
      <Route
        path="/hr-dashboard"
        element={
          <RoleRoute allowedRoles={["hr", "admin"]}>
            <HRDashboard />
          </RoleRoute>
        }
      />
      <Route
        path="/manager-dashboard"
        element={
          <RoleRoute allowedRoles={["manager", "admin"]}>
            <ManagerDashboard />
          </RoleRoute>
        }
      />
      <Route
        path="/employee-dashboard"
        element={
          <RoleRoute allowedRoles={["employee", "admin"]}>
            <EmployeeDashboard />
          </RoleRoute>
        }
      />

      {/* Shared protected routes */}
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