import { Link } from "react-router";
import styles from "./Wordmark.module.css";

export function Wordmark({ to }: { to?: string }) {
  const mark = (
    <>
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
      Enterprise RAG
    </>
  );
  return to ? (
    <Link to={to} className={styles.wordmark}>
      {mark}
    </Link>
  ) : (
    <span className={styles.wordmark}>{mark}</span>
  );
}
