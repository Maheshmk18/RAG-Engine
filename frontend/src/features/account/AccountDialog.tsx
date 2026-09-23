import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import type { FormEvent } from "react";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { Field, Input } from "@/components/ui/Field";
import { api, ApiError } from "@/lib/api";
import { useAuth, useCurrentUser } from "@/lib/authContext";
import styles from "./AccountDialog.module.css";

function ProfileForm() {
  const user = useCurrentUser();
  const { replaceUser } = useAuth();
  const [name, setName] = useState(user.full_name);
  const save = useMutation({ mutationFn: () => api.updateProfile(name), onSuccess: replaceUser });

  return (
    <form
      className={styles.section}
      onSubmit={(event: FormEvent) => {
        event.preventDefault();
        save.mutate();
      }}
    >
      <Field label="Name" error={save.error?.message}>
        {(id) => <Input id={id} value={name} onChange={(event) => setName(event.target.value)} />}
      </Field>
      <div className={styles.actions}>
        {save.isSuccess && <span className={styles.saved}>Saved</span>}
        <Button type="submit" loading={save.isPending} disabled={name.trim() === user.full_name}>
          Save name
        </Button>
      </div>
    </form>
  );
}

function PasswordForm() {
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const change = useMutation({
    mutationFn: () => api.changePassword(current, next),
    onSuccess: () => {
      setCurrent("");
      setNext("");
    },
  });
  const fieldErrors = change.error instanceof ApiError ? change.error.fields : {};

  return (
    <form
      className={styles.section}
      onSubmit={(event: FormEvent) => {
        event.preventDefault();
        change.mutate();
      }}
    >
      <Field
        label="Current password"
        error={
          change.error?.message && !fieldErrors.new_password ? change.error.message : undefined
        }
      >
        {(id) => (
          <Input
            id={id}
            type="password"
            autoComplete="current-password"
            value={current}
            onChange={(event) => setCurrent(event.target.value)}
          />
        )}
      </Field>
      <Field
        label="New password"
        hint="At least 12 characters, mixing letters with numbers or symbols."
        error={fieldErrors.new_password}
      >
        {(id, describedBy) => (
          <Input
            id={id}
            type="password"
            autoComplete="new-password"
            aria-describedby={describedBy}
            value={next}
            onChange={(event) => setNext(event.target.value)}
          />
        )}
      </Field>
      <div className={styles.actions}>
        {change.isSuccess && <span className={styles.saved}>Password updated</span>}
        <Button type="submit" loading={change.isPending} disabled={!current || !next}>
          Change password
        </Button>
      </div>
    </form>
  );
}

export function AccountDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const user = useCurrentUser();
  return (
    <Dialog open={open} onClose={onClose} title="Account settings" description={user.email}>
      {open && (
        <>
          <ProfileForm />
          <PasswordForm />
        </>
      )}
    </Dialog>
  );
}
