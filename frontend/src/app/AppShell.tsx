import { useQuery } from "@tanstack/react-query";
import {
  FileText,
  LogOut,
  Microscope,
  Monitor,
  Moon,
  PanelLeft,
  Plus,
  Settings,
  Sun,
  Users,
} from "lucide-react";
import { Suspense, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router";
import { Button, IconButton } from "@/components/ui/Button";
import { Menu, MenuItem, MenuSection } from "@/components/ui/Menu";
import { Spinner } from "@/components/ui/Spinner";
import { AccountDialog } from "@/features/account/AccountDialog";
import { AnswerStreamProvider } from "@/features/chat/AnswerStreamProvider";
import { ConversationList } from "@/features/chat/ConversationList";
import { api } from "@/lib/api";
import { useAuth, useCurrentUser } from "@/lib/authContext";
import { initials } from "@/lib/format";
import { useTheme } from "@/lib/theme";
import type { Theme } from "@/lib/theme";
import styles from "./AppShell.module.css";

const THEMES: { value: Theme; label: string; icon: typeof Sun }[] = [
  { value: "system", label: "System", icon: Monitor },
  { value: "light", label: "Light", icon: Sun },
  { value: "dark", label: "Dark", icon: Moon },
];

export function Wordmark() {
  return (
    <span className={styles.wordmark}>
      <svg viewBox="0 0 32 32" width="22" height="22" aria-hidden="true">
        <rect width="32" height="32" rx="7" fill="var(--accent)" />
        <path
          d="M10 8.5h8.5L23 13v10.5H10z"
          fill="none"
          stroke="var(--on-accent)"
          strokeWidth="2"
          strokeLinejoin="round"
        />
        <path
          d="M13.5 17h6M13.5 20.5h4"
          stroke="var(--on-accent)"
          strokeWidth="2"
          strokeLinecap="round"
        />
      </svg>
      Ask My Docs
    </span>
  );
}

function AccountMenu({ onOpenSettings }: { onOpenSettings: () => void }) {
  const user = useCurrentUser();
  const { signOut } = useAuth();
  const [theme, setTheme] = useTheme();

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
          <MenuSection label="Appearance">
            <div className={styles.themes} role="radiogroup" aria-label="Theme">
              {THEMES.map(({ value, label, icon: Icon }) => (
                <button
                  key={value}
                  type="button"
                  role="radio"
                  aria-checked={theme === value}
                  className={styles.theme}
                  onClick={() => setTheme(value)}
                >
                  <Icon size={14} />
                  {label}
                </button>
              ))}
            </div>
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
          <Wordmark />
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
