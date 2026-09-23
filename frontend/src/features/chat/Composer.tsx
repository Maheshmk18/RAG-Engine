import { ArrowUp, Square } from "lucide-react";
import { useLayoutEffect, useRef, useState } from "react";
import type { FormEvent, KeyboardEvent } from "react";
import styles from "./Composer.module.css";

const MAX_LENGTH = 2000;

interface ComposerProps {
  busy: boolean;
  onSend: (text: string) => void;
  onStop: () => void;
  autoFocus?: boolean;
}

export function Composer({ busy, onSend, onStop, autoFocus }: ComposerProps) {
  const [text, setText] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);

  useLayoutEffect(() => {
    const element = ref.current;
    if (!element) return;
    element.style.height = "auto";
    element.style.height = `${Math.min(element.scrollHeight, 200)}px`;
  }, [text]);

  function submit(event?: FormEvent) {
    event?.preventDefault();
    const question = text.trim();
    if (!question || busy) return;
    onSend(question);
    setText("");
  }

  function handleKey(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      submit();
    }
  }

  return (
    <form className={styles.composer} onSubmit={submit}>
      <label htmlFor="question" className="visually-hidden">
        Ask a question
      </label>
      <textarea
        id="question"
        ref={ref}
        rows={1}
        value={text}
        maxLength={MAX_LENGTH}
        placeholder="Ask about a policy, process or guideline"
        onChange={(event) => setText(event.target.value)}
        onKeyDown={handleKey}
        autoFocus={autoFocus}
      />
      {busy ? (
        <button type="button" className={styles.send} onClick={onStop} aria-label="Stop answering">
          <Square size={12} fill="currentColor" />
        </button>
      ) : (
        <button type="submit" className={styles.send} disabled={!text.trim()} aria-label="Send">
          <ArrowUp size={16} />
        </button>
      )}
    </form>
  );
}
