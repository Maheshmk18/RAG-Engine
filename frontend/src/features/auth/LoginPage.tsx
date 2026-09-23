import { useState } from "react";
import type { FormEvent } from "react";
import { Navigate, useLocation, useNavigate } from "react-router";
import { Wordmark } from "@/app/AppShell";
import { Button } from "@/components/ui/Button";
import { Field, Input } from "@/components/ui/Field";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/authContext";
import styles from "./LoginPage.module.css";

export function LoginPage() {
  const { status, signIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const destination = (location.state as { from?: string } | null)?.from ?? "/chat";
  if (status === "signed-in") return <Navigate to={destination} replace />;

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await signIn(email, password);
      navigate(destination, { replace: true });
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "We could not reach the server.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className={styles.page}>
      <div className={styles.brand}>
        <Wordmark />
      </div>
      <form className={styles.form} onSubmit={submit} noValidate>
        <div className={styles.heading}>
          <h1>Sign in</h1>
          <p className="muted">Use the account your administrator set up for you.</p>
        </div>
        <Field label="Email">
          {(id) => (
            <Input
              id={id}
              type="email"
              autoComplete="username"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
              autoFocus
            />
          )}
        </Field>
        <Field label="Password">
          {(id) => (
            <Input
              id={id}
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          )}
        </Field>
        {error && (
          <p className={styles.error} role="alert">
            {error}
          </p>
        )}
        <Button
          type="submit"
          variant="primary"
          loading={submitting}
          disabled={!email || !password}
          className={styles.submit}
        >
          Sign in
        </Button>
      </form>
      <p className={styles.note}>
        Answers come from your organisation&apos;s documents and link to the passage they are based
        on.
      </p>
    </main>
  );
}
