import { useQuery } from "@tanstack/react-query";
import { FileText, LogOut, Microscope, PanelLeft, Plus, Settings, Users } from "lucide-react";
import { Suspense, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router";
import { Button, IconButton } from "@/components/ui/Button";
import { Menu, MenuItem, MenuSection } from "@/components/ui/Menu";
import { Spinner } from "@/components/ui/Spinner";
import { Wordmark } from "@/components/Wordmark";
import { AccountDialog } from "@/features/account/AccountDialog";
import { AnswerStreamProvider } from "@/features/chat/AnswerStreamProvider";
import { ConversationList } from "@/features/chat/ConversationList";
import { api } from "@/lib/api";
import { useAuth, useCurrentUser } from "@/lib/authContext";
import { initials } from "@/lib/format";
import styles from "./AppShell.module.css";

function AccountMenu({ onOpenSettings }: { onOpenSettings: () => void }) {
  const user = useCurrentUser();
  const { signOut } = useAuth();

  return (
    <Menu
      placement="above"
      trigger={({ toggle, open }) => (
        <button type="button" className={styles.account} onClick={toggle} aria-expanded={open}>
          <span className={styles.avatar}>{initials(user.full_name)}</span>
          <span className={styles.accountText}>
            <span className={styles.accountName}>{user.full_name}</span>
            <span className={styles.accountRole}>
              {user.role === "admin" ? "Administrator" : "Member"}
            </span>
          </span>
        </button>
      )}
    >
      {(close) => (
        <>
          <MenuSection label={user.email}>
            <MenuItem
              icon={<Settings size={15} />}
              onSelect={() => {
                close();
                onOpenSettings();
              }}
            >
              Account settings
            </MenuItem>
          </MenuSection>
          <MenuSection>
            <MenuItem icon={<LogOut size={15} />} onSelect={signOut}>
              Sign out
            </MenuItem>
          </MenuSection>
        </>
      )}
    </Menu>
  );
}

export function AppShell() {
  const user = useCurrentUser();
  const navigate = useNavigate();
  const location = useLocation();
  const [navOpen, setNavOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
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
          <Wordmark to="/chat" />
        </div>
        <div className={styles.newChat}>
          <Button
            icon={<Plus size={15} />}
            onClick={() => navigate("/chat")}
            className={styles.fill}
          >
            New conversation
          </Button>
        </div>
        <ConversationList sessions={sessions.data ?? []} loading={sessions.isPending} />
        <nav className={styles.nav} aria-label="Workspace">
          <NavLink to="/documents" className={navClass}>
            <FileText size={15} />
            Documents
          </NavLink>
          {user.role === "admin" && (
            <>
              <NavLink to="/admin/users" className={navClass}>
                <Users size={15} />
                People
              </NavLink>
              <NavLink to="/admin/search" className={navClass}>
                <Microscope size={15} />
                Search inspector
              </NavLink>
            </>
          )}
        </nav>
        <div className={styles.footer}>
          <AccountMenu onOpenSettings={() => setSettingsOpen(true)} />
        </div>
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
          <Wordmark />
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
      <AccountDialog open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
  );
}
