import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useLayoutEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router";
import { Spinner } from "@/components/ui/Spinner";
import { api } from "@/lib/api";
import type { Citation, Message, Session } from "@/lib/types";
import { useSharedAnswerStream } from "./answerStreamContext";
import { Composer } from "./Composer";
import { SourcePanel } from "./SourcePanel";
import { Answer, DraftAnswer, Interrupted, Question } from "./Turn";
import type { Selection } from "./Turn";
import styles from "./ChatPage.module.css";

const EXAMPLES = [
  "How many days of annual leave do I get?",
  "What is the hotel limit for business travel?",
  "What should I do if I lose my laptop?",
  "When do salary increases take effect?",
];

function Welcome({ onPick }: { onPick: (question: string) => void }) {
  const documents = useQuery({ queryKey: ["documents"], queryFn: api.documents });
  const ready = documents.data?.filter((item) => item.status === "ready").length ?? 0;

  return (
    <div className={styles.welcome}>
      <h1>What would you like to know?</h1>
      <p className="muted">
        {documents.isPending
          ? "Answers are drawn from your organisation's documents."
          : `Answers are drawn from ${ready} ${ready === 1 ? "document" : "documents"}, and every claim links to its source.`}
      </p>
      <div className={styles.examples}>
        {EXAMPLES.map((example) => (
          <button
            key={example}
            type="button"
            className={styles.example}
            onClick={() => onPick(example)}
          >
            {example}
          </button>
        ))}
      </div>
    </div>
  );
}

function pairTurns(messages: Message[]) {
  const turns: { question: Message; answer?: Message }[] = [];
  for (const message of messages) {
    if (message.role === "user") turns.push({ question: message });
    else if (turns.length > 0) {
      const last = turns[turns.length - 1];
      if (last && !last.answer) last.answer = message;
    }
  }
  return turns;
}

export function ChatPage() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const stream = useSharedAnswerStream();
  const [selection, setSelection] = useState<Selection | null>(null);
  const scroller = useRef<HTMLDivElement>(null);
  const pinned = useRef(true);

  const conversation = useQuery({
    queryKey: ["session", sessionId],
    queryFn: () => api.session(sessionId as string),
    enabled: Boolean(sessionId),
  });

  const [viewedSession, setViewedSession] = useState(sessionId);
  if (viewedSession !== sessionId) {
    setViewedSession(sessionId);
    setSelection(null);
  }

  const draft = stream.draft?.sessionId === sessionId ? stream.draft : null;
  const messages = conversation.data?.messages ?? [];
  const turns = pairTurns(messages);
  const lastTurn = turns.at(-1);
  const draftInTurn = Boolean(
    draft && lastTurn && !lastTurn.answer && lastTurn.question.content === draft.question,
  );

  useLayoutEffect(() => {
    const element = scroller.current;
    if (element && pinned.current) element.scrollTop = element.scrollHeight;
  }, [messages.length, draft?.text, draft?.phase]);

  async function send(question: string) {
    pinned.current = true;
    setSelection(null);
    let target = sessionId;
    if (!target) {
      const created = await api.createSession();
      queryClient.setQueryData<Session[]>(["sessions"], (current) => [created, ...(current ?? [])]);
      queryClient.setQueryData(["session", created.id], { ...created, messages: [] });
      target = created.id;
      navigate(`/chat/${created.id}`);
    }
    await stream.ask(target, question);
  }

  const retry = (question: string) => {
    stream.dismiss();
    void send(question);
  };

  const citation: Citation | undefined = selection
    ? messages
        .find((message) => message.id === selection.messageId)
        ?.citations.find((item) => item.number === selection.number)
    : undefined;

  const busy = Boolean(draft && draft.phase !== "failed");
  const empty = !sessionId && !draft;

  return (
    <div className={styles.layout}>
      <section className={styles.conversation}>
        <div
          className={styles.scroller}
          ref={scroller}
          onScroll={(event) => {
            const element = event.currentTarget;
            pinned.current = element.scrollHeight - element.scrollTop - element.clientHeight < 80;
          }}
        >
          <div className={styles.column}>
            {empty && <Welcome onPick={(question) => void send(question)} />}
            {sessionId && conversation.isPending && (
              <div className={styles.loading}>
                <Spinner size={18} label="Loading conversation" />
              </div>
            )}
            {conversation.isError && (
              <p className={styles.missing}>This conversation could not be found.</p>
            )}
            {turns.map(({ question, answer }) => {
              const isLast = question.id === lastTurn?.question.id;
              return (
                <article key={question.id} className={styles.turn}>
                  <Question text={question.content} />
                  {answer && (
                    <Answer
                      message={answer}
                      sessionId={sessionId as string}
                      selection={selection}
                      onSelect={setSelection}
                      onRetry={isLast && !draft ? () => retry(question.content) : undefined}
                    />
                  )}
                  {!answer && isLast && draftInTurn && draft && (
                    <DraftAnswer draft={draft} onRetry={() => retry(draft.question)} />
                  )}
                  {!answer && !(isLast && draftInTurn) && (
                    <Interrupted
                      onRetry={isLast && !draft ? () => retry(question.content) : undefined}
                    />
                  )}
                </article>
              );
            })}
            {draft && !draftInTurn && (
              <article className={styles.turn}>
                <Question text={draft.question} />
                <DraftAnswer draft={draft} onRetry={() => retry(draft.question)} />
              </article>
            )}
          </div>
        </div>
        <div className={styles.dock}>
          <div className={styles.column}>
            <Composer
              busy={busy}
              onSend={(question) => void send(question)}
              onStop={stream.stop}
              autoFocus
            />
            <p className={styles.disclaimer}>
              Answers are generated from your documents. Check the cited source before acting on it.
            </p>
          </div>
        </div>
      </section>
      {citation && <SourcePanel citation={citation} onClose={() => setSelection(null)} />}
    </div>
  );
}
