import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Lock, RotateCw, ShieldCheck, Trash2 } from "lucide-react";
import { useState } from "react";
import { Badge } from "@/components/ui/Badge";
import type { Tone } from "@/components/ui/Badge";
import { Button, IconButton } from "@/components/ui/Button";
import { EmptyState, PageHeader } from "@/components/ui/PageHeader";
import { Spinner } from "@/components/ui/Spinner";
import table from "@/components/ui/Table.module.css";
import { useAdminAccess } from "@/lib/admin";
import { api } from "@/lib/api";
import { formatBytes, formatDate, timeAgo } from "@/lib/format";
import type { DocumentItem, DocumentStatus } from "@/lib/types";
import { AdminKeyDialog } from "./AdminKeyDialog";
import { UploadPanel } from "./UploadPanel";
import upload from "./UploadPanel.module.css";
import { useUploader } from "./useUploader";
import styles from "./DocumentsPage.module.css";

const STATUS: Record<DocumentStatus, { label: string; tone: Tone }> = {
  pending: { label: "Queued", tone: "neutral" },
  processing: { label: "Indexing", tone: "warning" },
  ready: { label: "Ready", tone: "success" },
  failed: { label: "Failed", tone: "danger" },
};

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
              if (window.confirm(`Remove "${document.title}" from the knowledge base?`)) {
                remove.mutate();
              }
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
  const { unlocked: canManage, lock } = useAdminAccess();
  const [unlocking, setUnlocking] = useState(false);
  const uploader = useUploader();

  const documents = useQuery({
    queryKey: ["documents"],
    queryFn: api.documents,
    refetchInterval: (query) =>
      query.state.data?.some((item) => item.status === "pending" || item.status === "processing")
        ? 2000
        : false,
  });

  const items = documents.data ?? [];
  const ready = items.filter((item) => item.status === "ready");
  const passages = ready.reduce((sum, item) => sum + item.chunk_count, 0);

  return (
    <div className={styles.page}>
      <PageHeader
        title="Documents"
        description={
          documents.isSuccess
            ? `${ready.length} of ${items.length} documents are searchable, split into ${passages} passages.`
            : "The knowledge base the assistant answers from."
        }
        actions={
          canManage && (
            <Button icon={<ShieldCheck size={15} />} onClick={lock}>
              Leave admin mode
            </Button>
          )
        }
      />

      <section aria-label="Upload documents">
        {canManage ? (
          <UploadPanel
            items={uploader.items}
            onFiles={(files) => void uploader.upload(files)}
            onDismiss={uploader.dismiss}
          />
        ) : (
          <div className={upload.locked}>
            <Lock size={18} />
            <div>
              <p className={upload.lockedTitle}>Upload documents</p>
              <p>Adding, re-indexing and removing documents needs the admin key.</p>
            </div>
            <Button variant="primary" onClick={() => setUnlocking(true)}>
              Unlock
            </Button>
          </div>
        )}
      </section>

      {documents.isPending ? (
        <div className={styles.loading}>
          <Spinner size={18} label="Loading documents" />
        </div>
      ) : items.length === 0 ? (
        <EmptyState title="No documents yet">
          Unlock with the admin key and upload a policy, handbook or guide to get started.
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
    </div>
  );
}
