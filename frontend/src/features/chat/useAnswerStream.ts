import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { readServerEvents } from "@/lib/sse";
import type { Message, SessionDetail } from "@/lib/types";

export interface Draft {
  sessionId: string;
  question: string;
  phase: "searching" | "writing" | "failed";
  documents: string[];
  text: string;
  error?: string;
}

function appendMessages(
  queryClient: ReturnType<typeof useQueryClient>,
  id: string,
  added: Message[],
) {
  queryClient.setQueryData<SessionDetail>(["session", id], (current) =>
    current
      ? {
          ...current,
          messages: [
            ...current.messages.filter((message) => !added.some((item) => item.id === message.id)),
            ...added,
          ],
        }
      : current,
  );
}

export function useAnswerStream() {
  const queryClient = useQueryClient();
  const [draft, setDraft] = useState<Draft | null>(null);
  const controller = useRef<AbortController | null>(null);

  useEffect(() => () => controller.current?.abort(), []);

  const stop = useCallback(() => {
    controller.current?.abort();
    controller.current = null;
    setDraft(null);
  }, []);

  const ask = useCallback(
    async (sessionId: string, question: string) => {
      controller.current?.abort();
      const abort = new AbortController();
      controller.current = abort;
      setDraft({ sessionId, question, phase: "searching", documents: [], text: "" });
      const update = (patch: Partial<Draft>) =>
        setDraft((current) => (current ? { ...current, ...patch } : current));

      try {
        const response = await api.ask(sessionId, question, abort.signal);
        for await (const { event, data } of readServerEvents(response)) {
          if (event === "question") {
            appendMessages(queryClient, sessionId, [data as Message]);
            void queryClient.invalidateQueries({ queryKey: ["sessions"] });
          } else if (event === "retrieval") {
            const { documents } = data as { documents: string[] };
            update({ phase: "writing", documents });
          } else if (event === "token") {
            const { text } = data as { text: string };
            setDraft((current) => (current ? { ...current, text: current.text + text } : current));
          } else if (event === "replace") {
            update({ text: (data as { text: string }).text });
          } else if (event === "answer" || event === "error") {
            appendMessages(queryClient, sessionId, [data as Message]);
            setDraft(null);
          }
        }
      } catch (caught) {
        if (abort.signal.aborted) return;
        const message =
          caught instanceof ApiError ? caught.message : "The connection was interrupted.";
        update({ phase: "failed", error: message });
      } finally {
        if (controller.current === abort) controller.current = null;
        queryClient.invalidateQueries({ queryKey: ["sessions"] });
      }
    },
    [queryClient],
  );

  return { draft, ask, stop, dismiss: () => setDraft(null) };
}
