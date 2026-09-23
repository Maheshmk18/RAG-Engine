import { useId } from "react";
import type { InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from "react";
import styles from "./Field.module.css";

interface FieldProps {
  label: string;
  hint?: string;
  error?: string;
  children: (id: string, describedBy: string | undefined) => ReactNode;
}

export function Field({ label, hint, error, children }: FieldProps) {
  const id = useId();
  const noteId = `${id}-note`;
  return (
    <div className={styles.field}>
      <label htmlFor={id} className={styles.label}>
        {label}
      </label>
      {children(id, hint || error ? noteId : undefined)}
      {error ? (
        <p id={noteId} className={styles.error}>
          {error}
        </p>
      ) : (
        hint && (
          <p id={noteId} className={styles.hint}>
            {hint}
          </p>
        )
      )}
    </div>
  );
}

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={[styles.control, className].filter(Boolean).join(" ")} {...props} />;
}

export function Select({ className, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select className={[styles.control, className].filter(Boolean).join(" ")} {...props} />;
}
