import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Check, CircleAlert, Copy, RotateCw, SearchX, ThumbsDown, ThumbsUp } from "lucide-react";
import { useState } from "react";
import { Button, IconButton } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { api } from "@/lib/api";
import type { Citation, Message, SessionDetail } from "@/lib/types";
import { Markdown } from "./Markdown";
import type { Draft } from "./useAnswerStream";
import styles from "./Turn.module.css";

export interface Selection {
  messageId: string;
  number: number;
}

export function Question({ text }: { text: string }) {
  return <p className={styles.question}>{text}</p>;
}

function stripCitations(text: string) {
  return text.replace(/\s?\[\d{1,2}\]/g, "");
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <IconButton
      label={copied ? "Copied" : "Copy answer"}
      onClick={async () => {
        await navigator.clipboard.writeText(stripCitations(text));
        setCopied(true);
        window.setTimeout(() => setCopied(false), 1500);
      }}
    >
      {copied ? <Check size={15} /> : <Copy size={15} />}
    </IconButton>
  );
}

function Feedback({ message, sessionId }: { message: Message; sessionId: string }) {
  const queryClient = useQueryClient();
  const rate = useMutation({
    mutationFn: (value: 1 | -1 | null) => api.feedback(message.id, value),
    onSuccess: (updated) =>
      queryClient.setQueryData<SessionDetail>(["session", sessionId], (current) =>
        current
          ? {
              ...current,
              messages: current.messages.map((item) => (item.id === updated.id ? updated : item)),
            }
          : current,
      ),
  });
  const toggle = (value: 1 | -1) => rate.mutate(message.feedback === value ? null : value);
  return (
    <>
      <IconButton label="Helpful" active={message.feedback === 1} onClick={() => toggle(1)}>
        <ThumbsUp size={15} />
      </IconButton>
      <IconButton label="Not helpful" active={message.feedback === -1} onClick={() => toggle(-1)}>
        <ThumbsDown size={15} />
      </IconButton>
    </>
  );
}

function SourceList({
  citations,
  selected,
  onSelect,
}: {
  citations: Citation[];
  selected: number | null;
  onSelect: (number: number) => void;
}) {
  return (
    <ol className={styles.sources} aria-label="Sources">
      {citations.map((citation) => (
        <li key={citation.number}>
          <button
            type="button"
            className={`${styles.source} ${selected === citation.number ? styles.sourceActive : ""}`}
            onClick={() => onSelect(citation.number)}
          >
            <span className={styles.sourceNumber}>{citation.number}</span>
            <span className={styles.sourceTitle}>{citation.document_title}</span>
            {citation.heading && <span className={styles.sourceHeading}>{citation.heading}</span>}
            {citation.page && <span className={styles.sourcePage}>p. {citation.page}</span>}
          </button>
        </li>
      ))}
    </ol>
  );
}

interface AnswerProps {
  message: Message;
  sessionId: string;
  selection: Selection | null;
  onSelect: (selection: Selection) => void;
  onRetry?: () => void;
}

export function Answer({ message, sessionId, selection, onSelect, onRetry }: AnswerProps) {
  if (message.status === "failed") {
    return (
      <div className={`${styles.notice} ${styles.failed}`} role="alert">
        <CircleAlert size={16} />
        <p>{message.content}</p>
        {onRetry && (
          <Button size="sm" icon={<RotateCw size={13} />} onClick={onRetry}>
            Try again
          </Button>
        )}
      </div>
    );
  }

  if (message.status === "abstained") {
    return (
      <div className={styles.notice}>
        <SearchX size={16} />
        <div>
          <p className={styles.noticeTitle}>Not covered by the documents</p>
          <p className="muted">{message.content}</p>
        </div>
      </div>
    );
  }

  const selected = selection?.messageId === message.id ? selection.number : null;
  const available = new Set(message.citations.map((citation) => citation.number));
  const select = (number: number) => onSelect({ messageId: message.id, number });

  return (
    <div className={styles.answer}>
      <Markdown text={message.content} available={available} active={selected} onCite={select} />
      {message.citations.length > 0 && (
        <SourceList citations={message.citations} selected={selected} onSelect={select} />
      )}
      <div className={styles.actions}>
        <CopyButton text={message.content} />
        <Feedback message={message} sessionId={sessionId} />
      </div>
    </div>
  );
}

export function DraftAnswer({ draft, onRetry }: { draft: Draft; onRetry: () => void }) {
  if (draft.phase === "failed") {
    return (
      <div className={`${styles.notice} ${styles.failed}`} role="alert">
        <CircleAlert size={16} />
        <p>{draft.error}</p>
        <Button size="sm" icon={<RotateCw size={13} />} onClick={onRetry}>
          Try again
        </Button>
      </div>
    );
  }

  if (!draft.text) {
    const reading = draft.documents.length > 0;
    return (
      <p className={styles.status} aria-live="polite">
        <Spinner size={13} />
        {reading ? `Reading ${draft.documents.join(", ")}` : "Searching the documents"}
      </p>
    );
  }

  return (
    <div className={`${styles.answer} ${styles.streaming}`} aria-live="polite" aria-busy="true">
      <Markdown text={draft.text} available={new Set()} />
    </div>
  );
}

export function Interrupted({ onRetry }: { onRetry?: () => void }) {
  return (
    <div className={styles.notice}>
      <CircleAlert size={16} />
      <p className={styles.grow}>This question was not answered.</p>
      {onRetry && (
        <Button size="sm" icon={<RotateCw size={13} />} onClick={onRetry}>
          Ask again
        </Button>
      )}
    </div>
  );
}
