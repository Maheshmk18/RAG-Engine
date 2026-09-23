import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Trash2, UserPlus } from "lucide-react";
import { useState } from "react";
import type { FormEvent } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button, IconButton } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { Field, Input, Select } from "@/components/ui/Field";
import { PageHeader } from "@/components/ui/PageHeader";
import { Spinner } from "@/components/ui/Spinner";
import table from "@/components/ui/Table.module.css";
import { api, ApiError } from "@/lib/api";
import { useCurrentUser } from "@/lib/authContext";
import { formatDate, timeAgo } from "@/lib/format";
import type { Role, User } from "@/lib/types";
import styles from "./AdminPages.module.css";

function AddPersonDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({
    email: "",
    full_name: "",
    password: "",
    role: "member" as Role,
  });
  const create = useMutation({
    mutationFn: () => api.createUser(form),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      setForm({ email: "", full_name: "", password: "", role: "member" });
      onClose();
    },
  });
  const errors = create.error instanceof ApiError ? create.error.fields : {};
  const general = create.error && Object.keys(errors).length === 0 ? create.error.message : null;
  const set = (key: keyof typeof form) => (value: string) =>
    setForm((current) => ({ ...current, [key]: value }));

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="Add a person"
      description="Share the temporary password with them directly. They can change it after signing in."
      footer={
        <>
          <Button onClick={onClose}>Cancel</Button>
          <Button variant="primary" type="submit" form="add-person" loading={create.isPending}>
            Add person
          </Button>
        </>
      }
    >
      <form
        id="add-person"
        className={styles.form}
        onSubmit={(event: FormEvent) => {
          event.preventDefault();
          create.mutate();
        }}
      >
        <Field label="Full name" error={errors.full_name}>
          {(id) => (
            <Input
              id={id}
              value={form.full_name}
              onChange={(event) => set("full_name")(event.target.value)}
            />
          )}
        </Field>
        <Field label="Email" error={errors.email}>
          {(id) => (
            <Input
              id={id}
              type="email"
              value={form.email}
              onChange={(event) => set("email")(event.target.value)}
            />
          )}
        </Field>
        <Field label="Role" hint="Administrators can manage documents and people.">
          {(id, describedBy) => (
            <Select
              id={id}
              aria-describedby={describedBy}
              value={form.role}
              onChange={(event) => set("role")(event.target.value)}
            >
              <option value="member">Member</option>
              <option value="admin">Administrator</option>
            </Select>
          )}
        </Field>
        <Field
          label="Temporary password"
          hint="At least 12 characters, mixing letters with numbers or symbols."
          error={errors.password}
        >
          {(id, describedBy) => (
            <Input
              id={id}
              aria-describedby={describedBy}
              value={form.password}
              autoComplete="new-password"
              onChange={(event) => set("password")(event.target.value)}
            />
          )}
        </Field>
        {general && <p className={styles.formError}>{general}</p>}
      </form>
    </Dialog>
  );
}

function PersonRow({ person, isSelf }: { person: User; isSelf: boolean }) {
  const queryClient = useQueryClient();
  const refresh = () => queryClient.invalidateQueries({ queryKey: ["users"] });
  const update = useMutation({
    mutationFn: (data: Partial<Pick<User, "role" | "is_active">>) =>
      api.updateUser(person.id, data),
    onSuccess: refresh,
    onError: (error) => window.alert(error.message),
  });
  const remove = useMutation({
    mutationFn: () => api.deleteUser(person.id),
    onSuccess: refresh,
    onError: (error) => window.alert(error.message),
  });

  return (
    <tr>
      <td>
        <span className={table.primary}>
          {person.full_name}
          {isSelf && <span className={styles.you}>You</span>}
        </span>
        <span className={table.secondary}>{person.email}</span>
      </td>
      <td>
        <select
          className={styles.inlineSelect}
          value={person.role}
          disabled={isSelf || update.isPending}
          aria-label={`Role for ${person.full_name}`}
          onChange={(event) => update.mutate({ role: event.target.value as Role })}
        >
          <option value="member">Member</option>
          <option value="admin">Administrator</option>
        </select>
      </td>
      <td>
        <Badge tone={person.is_active ? "success" : "neutral"}>
          {person.is_active ? "Active" : "Deactivated"}
        </Badge>
      </td>
      <td>
        {person.last_login_at ? (
          <span title={formatDate(person.last_login_at)}>{timeAgo(person.last_login_at)}</span>
        ) : (
          <span className="muted">Never</span>
        )}
      </td>
      <td className={table.actions}>
        {!isSelf && (
          <>
            <Button
              size="sm"
              variant="ghost"
              disabled={update.isPending}
              onClick={() => update.mutate({ is_active: !person.is_active })}
            >
              {person.is_active ? "Deactivate" : "Reactivate"}
            </Button>
            <IconButton
              label={`Delete ${person.full_name}`}
              disabled={remove.isPending}
              onClick={() => {
                if (window.confirm(`Delete ${person.full_name}'s account and conversations?`))
                  remove.mutate();
              }}
            >
              <Trash2 size={15} />
            </IconButton>
          </>
        )}
      </td>
    </tr>
  );
}

export function UsersPage() {
  const me = useCurrentUser();
  const [adding, setAdding] = useState(false);
  const people = useQuery({ queryKey: ["users"], queryFn: api.users });

  return (
    <div className={styles.page}>
      <PageHeader
        title="People"
        description="Everyone who can sign in. Members can ask questions; administrators also manage documents and accounts."
        actions={
          <Button variant="primary" icon={<UserPlus size={15} />} onClick={() => setAdding(true)}>
            Add person
          </Button>
        }
      />
      {people.isPending ? (
        <div className={styles.loading}>
          <Spinner size={18} label="Loading people" />
        </div>
      ) : (
        <div className={table.wrap}>
          <table className={table.table}>
            <thead>
              <tr>
                <th>Name</th>
                <th>Role</th>
                <th>Status</th>
                <th>Last sign-in</th>
                <th className={table.actions}>
                  <span className="visually-hidden">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {people.data?.map((person) => (
                <PersonRow key={person.id} person={person} isSelf={person.id === me.id} />
              ))}
            </tbody>
          </table>
        </div>
      )}
      <AddPersonDialog open={adding} onClose={() => setAdding(false)} />
    </div>
  );
}
