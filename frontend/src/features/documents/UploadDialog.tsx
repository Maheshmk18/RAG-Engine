import { Link } from "react-router";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { useAdminAccess } from "@/lib/admin";
import { AdminKeyForm } from "./AdminKeyDialog";
import { UploadPanel } from "./UploadPanel";
import styles from "./UploadPanel.module.css";
import { useUploader } from "./useUploader";

export function UploadDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { unlocked } = useAdminAccess();
  const uploader = useUploader();

  const close = () => {
    if (!uploader.busy) uploader.clear();
    onClose();
  };

  return (
    <Dialog
      open={open}
      onClose={close}
      title="Upload documents"
      description={
        unlocked
          ? "Added files are indexed in the background and can be asked about within seconds."
          : "Enter the admin key to add documents to the knowledge base."
      }
      footer={
        unlocked && (
          <>
            <Link to="/documents" onClick={close} className={styles.footerLink}>
              View all documents
            </Link>
            <Button variant="primary" onClick={close}>
              Done
            </Button>
          </>
        )
      }
    >
      {!open ? null : unlocked ? (
        <UploadPanel
          items={uploader.items}
          onFiles={(files) => void uploader.upload(files)}
          onDismiss={uploader.dismiss}
          compact
        />
      ) : (
        <AdminKeyForm />
      )}
    </Dialog>
  );
}
