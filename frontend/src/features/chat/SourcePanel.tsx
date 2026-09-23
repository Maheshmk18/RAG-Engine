import { ExternalLink, X } from "lucide-react";
import { useState } from "react";
import { Button, IconButton } from "@/components/ui/Button";
import { api } from "@/lib/api";
import type { Citation } from "@/lib/types";
import styles from "./SourcePanel.module.css";

async function openOriginal(documentId: string) {
  const blob = await api.documentFile(documentId);
  const url = URL.createObjectURL(blob);
  window.open(url, "_blank", "noopener");
  window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
}

export function SourcePanel({ citation, onClose }: { citation: Citation; onClose: () => void }) {
  const [opening, setOpening] = useState(false);

  return (
    <aside className={styles.panel} aria-label={`Source ${citation.number}`}>
      <header className={styles.header}>
        <span className={styles.eyebrow}>Source {citation.number}</span>
        <IconButton label="Close source" onClick={onClose}>
          <X size={16} />
        </IconButton>
      </header>
      <div className={styles.body}>
        <h2 className={styles.title}>{citation.document_title}</h2>
        {(citation.heading || citation.page) && (
          <p className={styles.location}>
            {citation.heading}
            {citation.heading && citation.page && " · "}
            {citation.page && `Page ${citation.page}`}
          </p>
        )}
        <blockquote className={styles.passage}>{citation.text}</blockquote>
      </div>
      <footer className={styles.footer}>
        <Button
          size="sm"
          icon={<ExternalLink size={13} />}
          loading={opening}
          onClick={async () => {
            setOpening(true);
            try {
              await openOriginal(citation.document_id);
            } finally {
              setOpening(false);
            }
          }}
        >
          Open original document
        </Button>
      </footer>
    </aside>
  );
}
