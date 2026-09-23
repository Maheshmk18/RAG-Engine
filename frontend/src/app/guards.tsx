import { Navigate, Outlet, useLocation } from "react-router";
import { Spinner } from "@/components/ui/Spinner";
import { useAuth } from "@/lib/authContext";
import styles from "./AppShell.module.css";

export function RequireAuth() {
  const { status } = useAuth();
  const location = useLocation();
  if (status === "loading") {
    return (
      <div className={styles.boot}>
        <Spinner size={20} label="Loading" />
      </div>
    );
  }
  if (status === "signed-out") {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return <Outlet />;
}

export function RequireAdmin() {
  const { user } = useAuth();
  return user?.role === "admin" ? <Outlet /> : <Navigate to="/chat" replace />;
}
