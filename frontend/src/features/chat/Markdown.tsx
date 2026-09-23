import ReactMarkdown from "react-markdown";
import type { Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import { remarkCitations } from "@/lib/remarkCitations";
import styles from "./Markdown.module.css";

interface MarkdownProps {
  text: string;
  available: Set<number>;
  active?: number | null;
  onCite?: (number: number) => void;
}

export function Markdown({ text, available, active, onCite }: MarkdownProps) {
  const components: Components = {
    cite: ({ node }) => {
      const number = Number(node?.properties?.dataNumber);
      const enabled = available.has(number) && onCite;
      return (
        <button
          type="button"
          className={`${styles.cite} ${active === number ? styles.citeActive : ""}`}
          disabled={!enabled}
          onClick={() => onCite?.(number)}
          aria-label={`Show source ${number}`}
        >
          {number}
        </button>
      );
    },
    a: ({ href, children }) => (
      <a href={href} target="_blank" rel="noreferrer">
        {children}
      </a>
    ),
  };

  return (
    <div className={styles.markdown}>
      <ReactMarkdown remarkPlugins={[remarkGfm, remarkCitations]} components={components}>
        {text}
      </ReactMarkdown>
    </div>
  );
}
