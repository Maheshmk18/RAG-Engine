import type { ReactNode } from "react";
import { AnswerStreamContext } from "./answerStreamContext";
import { useAnswerStream } from "./useAnswerStream";

export function AnswerStreamProvider({ children }: { children: ReactNode }) {
  const stream = useAnswerStream();
  return <AnswerStreamContext.Provider value={stream}>{children}</AnswerStreamContext.Provider>;
}
