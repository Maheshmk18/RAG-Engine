import type { ButtonHTMLAttributes, ReactNode } from "react";
import styles from "./Button.module.css";
import { Spinner } from "./Spinner";

type Variant = "primary" | "secondary" | "ghost" | "danger";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: "sm" | "md";
  icon?: ReactNode;
  loading?: boolean;
}

export function Button({
  variant = "secondary",
  size = "md",
  icon,
  loading = false,
  className,
  children,
  disabled,
  type = "button",
  ...props
}: ButtonProps) {
  const classes = [styles.button, styles[variant], styles[size], className].filter(Boolean);
  return (
    <button type={type} className={classes.join(" ")} disabled={disabled || loading} {...props}>
      {loading ? <Spinner size={14} /> : icon}
      {children}
    </button>
  );
}

interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  label: string;
  active?: boolean;
}

export function IconButton({
  label,
  active,
  className,
  type = "button",
  ...props
}: IconButtonProps) {
  const classes = [styles.iconButton, active && styles.active, className].filter(Boolean);
  return (
    <button type={type} aria-label={label} title={label} className={classes.join(" ")} {...props} />
  );
}
