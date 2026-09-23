import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Lock, RotateCw, Trash2, Upload, X } from "lucide-react";
import { useRef, useState } from "react";
import type { DragEvent } from "react";
import { Badge } from "@/components/ui/Badge";
import type { Tone } from "@/components/ui/Badge";
import { Button, IconButton } from "@/components/ui/Button";
import { EmptyState, PageHeader } from "@/components/ui/PageHeader";
import { Spinner } from "@/components/ui/Spinner";
import table from "@/components/ui/Table.module.css";
import { api, ApiError } from "@/lib/api";
import { useAdminAccess } from "@/lib/admin";
import { formatBytes, formatDate, timeAgo } from "@/lib/format";
import type { DocumentItem, DocumentStatus } from "@/lib/types";
import { AdminKeyDialog } from "./AdminKeyDialog";
import styles from "./DocumentsPage.module.css";

const ACCEPT = ".pdf,.docx,.md,.markdown,.txt";

const STATUS: Record<DocumentStatus, { label: string; tone: Tone }> = {
  pending: { label: "Queued", tone: "neutral" },
  processing: { label: "Indexing", tone: "warning" },
  ready: { label: "Ready", tone: "success" },
  failed: { label: "Failed", tone: "danger" },
};

interface UploadNotice {
  name: string;
  state: "uploading" | "done" | "error";
  message?: string;
}

function DocumentRow({ document, canManage }: { document: DocumentItem; canManage: boolean }) {
  const queryClient = useQueryClient();
  const refresh = () => queryClient.invalidateQueries({ queryKey: ["documents"] });
  const reprocess = useMutation({
    mutationFn: () => api.reprocessDocument(document.id),
    onSuccess: refresh,
  });
  const remove = useMutation({
    mutationFn: () => api.deleteDocument(document.id),
    onSuccess: refresh,
  });
  const status = STATUS[document.status];
  const busy = document.status === "pending" || document.status === "processing";

  return (
    <tr>
      <td>
        <span className={table.primary}>{document.title}</span>
        <span className={table.secondary}>{document.filename}</span>
      </td>
      <td>
        <Badge tone={status.tone}>{status.label}</Badge>
        {document.error_message && document.status === "failed" && (
          <span className={styles.error}>{document.error_message}</span>
        )}
      </td>
      <td className={table.numeric}>{document.status === "ready" ? document.chunk_count : "–"}</td>
      <td className={table.numeric}>{formatBytes(document.size_bytes)}</td>
      <td>
        <span title={formatDate(document.created_at)}>{timeAgo(document.created_at)}</span>
      </td>
      {canManage && (
        <td className={table.actions}>
          <IconButton
            label="Index again"
            disabled={busy || reprocess.isPending}
            onClick={() => reprocess.mutate()}
          >
            <RotateCw size={15} />
          </IconButton>
          <IconButton
            label="Delete"
            disabled={remove.isPending}
            onClick={() => {
              if (window.confirm(`Remove "${document.title}" from the knowledge base?`))
                remove.mutate();
            }}
          >
            <Trash2 size={15} />
          </IconButton>
        </td>
      )}
    </tr>
  );
}

export function DocumentsPage() {
  const { unlocked: canManage } = useAdminAccess();
  const [unlocking, setUnlocking] = useState(false);
  const queryClient = useQueryClient();
  const input = useRef<HTMLInputElement>(null);
  const [notices, setNotices] = useState<UploadNotice[]>([]);
  const [dragging, setDragging] = useState(false);

  const documents = useQuery({
    queryKey: ["documents"],
    queryFn: api.documents,
    refetchInterval: (query) =>
      query.state.data?.some((item) => item.status === "pending" || item.status === "processing")
        ? 2000
        : false,
  });

  async function upload(files: FileList | File[]) {
    const list = Array.from(files);
    setNotices(list.map((file) => ({ name: file.name, state: "uploading" })));
    await Promise.all(
      list.map(async (file) => {
        let notice: UploadNotice;
        try {
          await api.uploadDocument(file);
          notice = { name: file.name, state: "done" };
        } catch (caught) {
          const message = caught instanceof ApiError ? caught.message : "Upload failed";
          notice = { name: file.name, state: "error", message };
        }
        setNotices((current) => current.map((item) => (item.name === file.name ? notice : item)));
      }),
    );
    await queryClient.invalidateQueries({ queryKey: ["documents"] });
    setNotices((current) => current.filter((item) => item.state === "error"));
  }

  const dropProps = canManage
    ? {
        onDragOver: (event: DragEvent) => {
          event.preventDefault();
          setDragging(true);
        },
        onDragLeave: (event: DragEvent) => {
          if (!event.currentTarget.contains(event.relatedTarget as Node)) setDragging(false);
        },
        onDrop: (event: DragEvent) => {
          event.preventDefault();
          setDragging(false);
          if (event.dataTransfer.files.length) void upload(event.dataTransfer.files);
        },
      }
    : {};

  const items = documents.data ?? [];
  const ready = items.filter((item) => item.status === "ready");
  const chunks = ready.reduce((sum, item) => sum + item.chunk_count, 0);

  return (
    <div className={styles.page} data-dragging={dragging} {...dropProps}>
      <PageHeader
        title="Documents"
        description={
          documents.isSuccess
            ? `${ready.length} of ${items.length} documents are searchable, split into ${chunks} passages.`
            : "The knowledge base the assistant answers from."
        }
        actions={
          canManage ? (
            <>
              <input
                ref={input}
                type="file"
                accept={ACCEPT}
                multiple
                hidden
                onChange={(event) => {
                  if (event.target.files?.length) void upload(event.target.files);
                  event.target.value = "";
                }}
              />
              <Button
                variant="primary"
                icon={<Upload size={15} />}
                onClick={() => input.current?.click()}
              >
                Upload
              </Button>
            </>
          ) : (
            <Button icon={<Lock size={14} />} onClick={() => setUnlocking(true)}>
              Manage documents
            </Button>
          )
        }
      />

      {notices.length > 0 && (
        <ul className={styles.notices}>
          {notices.map((notice) => (
            <li key={notice.name} className={styles.notice} data-state={notice.state}>
              {notice.state === "uploading" && <Spinner size={13} />}
              <span className="mono">{notice.name}</span>
              <span>{notice.state === "uploading" ? "Uploading" : notice.message}</span>
              {notice.state === "error" && (
                <IconButton
                  label="Dismiss"
                  onClick={() => setNotices((current) => current.filter((item) => item !== notice))}
                >
                  <X size={14} />
                </IconButton>
              )}
            </li>
          ))}
        </ul>
      )}

      {documents.isPending ? (
        <div className={styles.loading}>
          <Spinner size={18} label="Loading documents" />
        </div>
      ) : items.length === 0 ? (
        <EmptyState title="No documents yet">
          {canManage
            ? "Upload PDF, Word, Markdown or text files. Drop them anywhere on this page."
            : "Unlock document management with the admin key to add the first documents."}
        </EmptyState>
      ) : (
        <div className={table.wrap}>
          <table className={table.table}>
            <thead>
              <tr>
                <th>Document</th>
                <th>Status</th>
                <th className={table.numeric}>Passages</th>
                <th className={table.numeric}>Size</th>
                <th>Added</th>
                {canManage && (
                  <th className={table.actions}>
                    <span className="visually-hidden">Actions</span>
                  </th>
                )}
              </tr>
            </thead>
            <tbody>
              {items.map((document) => (
                <DocumentRow key={document.id} document={document} canManage={canManage} />
              ))}
            </tbody>
          </table>
        </div>
      )}

      <AdminKeyDialog open={unlocking} onClose={() => setUnlocking(false)} />

      {canManage && (
        <p className={styles.help}>
          Supported formats: PDF, DOCX, Markdown and plain text, up to 20 MB each. Files are checked
          for duplicates and indexed in the background.
        </p>
      )}
    </div>
  );
}
