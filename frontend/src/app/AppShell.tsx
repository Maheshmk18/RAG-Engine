import { useQuery } from "@tanstack/react-query";
import { FileText, Microscope, PanelLeft, Plus, Upload } from "lucide-react";
import { Suspense, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router";
import { Button, IconButton } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { Wordmark } from "@/components/Wordmark";
import { AnswerStreamProvider } from "@/features/chat/AnswerStreamProvider";
import { ConversationList } from "@/features/chat/ConversationList";
import { UploadDialog } from "@/features/documents/UploadDialog";
import { api } from "@/lib/api";
import styles from "./AppShell.module.css";

export function AppShell() {
  const navigate = useNavigate();
  const location = useLocation();
  const [navOpen, setNavOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const sessions = useQuery({ queryKey: ["sessions"], queryFn: api.sessions });

  const [lastPath, setLastPath] = useState(location.pathname);
  if (lastPath !== location.pathname) {
    setLastPath(location.pathname);
    setNavOpen(false);
  }

  const navClass = ({ isActive }: { isActive: boolean }) =>
    `${styles.navLink} ${isActive ? styles.navActive : ""}`;

  return (
    <div className={styles.shell} data-nav-open={navOpen}>
      <aside className={styles.sidebar}>
        <div className={styles.brand}>
          <Wordmark to="/" />
        </div>
        <div className={styles.newChat}>
          <Button
            icon={<Plus size={15} />}
            onClick={() => navigate("/chat")}
            className={styles.fill}
          >
            New conversation
          </Button>
          <Button
            variant="ghost"
            icon={<Upload size={15} />}
            onClick={() => setUploading(true)}
            className={styles.fill}
          >
            Upload documents
          </Button>
        </div>
        <ConversationList sessions={sessions.data ?? []} loading={sessions.isPending} />
        <nav className={styles.nav} aria-label="Workspace">
          <NavLink to="/documents" className={navClass}>
            <FileText size={15} />
            Documents
          </NavLink>
          <NavLink to="/search" className={navClass}>
            <Microscope size={15} />
            Search inspector
          </NavLink>
        </nav>
      </aside>
      <button
        type="button"
        className={styles.scrim}
        aria-label="Close navigation"
        onClick={() => setNavOpen(false)}
      />
      <div className={styles.main}>
        <header className={styles.topbar}>
          <IconButton label="Open navigation" onClick={() => setNavOpen(true)}>
            <PanelLeft size={17} />
          </IconButton>
          <Wordmark to="/" />
        </header>
        <AnswerStreamProvider>
          <Suspense
            fallback={
              <div className={styles.boot}>
                <Spinner size={18} label="Loading" />
              </div>
            }
          >
            <Outlet />
          </Suspense>
        </AnswerStreamProvider>
      </div>
      <UploadDialog open={uploading} onClose={() => setUploading(false)} />
    </div>
  );
}
