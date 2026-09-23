import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import styles from "./Menu.module.css";

interface MenuProps {
  trigger: (props: { open: boolean; toggle: () => void }) => ReactNode;
  children: (close: () => void) => ReactNode;
  placement?: "above" | "below";
}

export function Menu({ trigger, children, placement = "below" }: MenuProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const dismiss = (event: MouseEvent | KeyboardEvent) => {
      if (
        event instanceof KeyboardEvent
          ? event.key === "Escape"
          : !ref.current?.contains(event.target as Node)
      ) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", dismiss);
    document.addEventListener("keydown", dismiss);
    return () => {
      document.removeEventListener("mousedown", dismiss);
      document.removeEventListener("keydown", dismiss);
    };
  }, [open]);

  return (
    <div className={styles.root} ref={ref}>
      {trigger({ open, toggle: () => setOpen((value) => !value) })}
      {open && (
        <div className={`${styles.menu} ${styles[placement]}`} role="menu">
          {children(() => setOpen(false))}
        </div>
      )}
    </div>
  );
}

interface MenuItemProps {
  icon?: ReactNode;
  children: ReactNode;
  onSelect: () => void;
  tone?: "default" | "danger";
}

export function MenuItem({ icon, children, onSelect, tone = "default" }: MenuItemProps) {
  return (
    <button
      type="button"
      role="menuitem"
      className={`${styles.item} ${tone === "danger" ? styles.danger : ""}`}
      onClick={onSelect}
    >
      {icon}
      {children}
    </button>
  );
}

export function MenuSection({ label, children }: { label?: string; children: ReactNode }) {
  return (
    <div className={styles.section}>
      {label && <p className={styles.label}>{label}</p>}
      {children}
    </div>
  );
}
