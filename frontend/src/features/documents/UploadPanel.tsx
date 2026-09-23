import { CircleAlert, CircleCheck, UploadCloud, X } from "lucide-react";
import { useRef, useState } from "react";
import type { DragEvent } from "react";
import { IconButton } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import type { UploadItem } from "./useUploader";
import { ACCEPTED_FILES } from "./useUploader";
import styles from "./UploadPanel.module.css";

interface UploadPanelProps {
  items: UploadItem[];
  onFiles: (files: FileList) => void;
  onDismiss: (name: string) => void;
  compact?: boolean;
}

export function UploadPanel({ items, onFiles, onDismiss, compact }: UploadPanelProps) {
  const input = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const drop = (event: DragEvent) => {
    event.preventDefault();
    setDragging(false);
    if (event.dataTransfer.files.length) onFiles(event.dataTransfer.files);
  };

  return (
    <div className={styles.panel}>
      <button
        type="button"
        className={`${styles.zone} ${compact ? styles.compact : ""}`}
        data-dragging={dragging}
        onClick={() => input.current?.click()}
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={drop}
      >
        <UploadCloud size={compact ? 18 : 22} />
        <span className={styles.zoneTitle}>
          {dragging ? "Drop to upload" : "Drop files here or choose from your computer"}
        </span>
        <span className={styles.zoneHint}>PDF, Word, Markdown or text, up to 20 MB each</span>
      </button>
      <input
        ref={input}
        type="file"
        accept={ACCEPTED_FILES}
        multiple
        hidden
        onChange={(event) => {
          if (event.target.files?.length) onFiles(event.target.files);
          event.target.value = "";
        }}
      />
      {items.length > 0 && (
        <ul className={styles.items}>
          {items.map((item) => (
            <li key={item.name} className={styles.item} data-state={item.state}>
              {item.state === "uploading" && <Spinner size={13} />}
              {item.state === "done" && <CircleCheck size={15} />}
              {item.state === "error" && <CircleAlert size={15} />}
              <span className={styles.name}>{item.name}</span>
              <span className={styles.status}>
                {item.state === "uploading" ? "Uploading" : item.message}
              </span>
              {item.state !== "uploading" && (
                <IconButton label="Dismiss" onClick={() => onDismiss(item.name)}>
                  <X size={14} />
                </IconButton>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
