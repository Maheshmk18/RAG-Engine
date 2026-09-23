import { useState } from "react";
import type { FormEvent } from "react";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { Field, Input } from "@/components/ui/Field";
import { useAdminAccess } from "@/lib/admin";
import { ApiError } from "@/lib/api";

export function AdminKeyDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { unlock } = useAdminAccess();
  const [key, setKey] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [checking, setChecking] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setChecking(true);
    setError(null);
    try {
      await unlock(key.trim());
      setKey("");
      onClose();
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "The server could not be reached.");
    } finally {
      setChecking(false);
    }
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="Manage documents"
      description="Uploading and removing documents needs the admin key configured on the server. It is kept only for this browser tab."
      footer={
        <>
          <Button onClick={onClose}>Cancel</Button>
          <Button
            variant="primary"
            type="submit"
            form="admin-key"
            loading={checking}
            disabled={!key.trim()}
          >
            Unlock
          </Button>
        </>
      }
    >
      <form id="admin-key" onSubmit={submit}>
        <Field label="Admin key" error={error ?? undefined}>
          {(id) => (
            <Input
              id={id}
              type="password"
              autoComplete="off"
              value={key}
              onChange={(event) => setKey(event.target.value)}
              aria-invalid={Boolean(error)}
              autoFocus
            />
          )}
        </Field>
      </form>
    </Dialog>
  );
}
