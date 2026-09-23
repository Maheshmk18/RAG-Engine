import { createContext, useContext } from "react";
import type { useAnswerStream } from "./useAnswerStream";

export type AnswerStream = ReturnType<typeof useAnswerStream>;

export const AnswerStreamContext = createContext<AnswerStream | null>(null);

export function useSharedAnswerStream(): AnswerStream {
  const context = useContext(AnswerStreamContext);
  if (!context) throw new Error("useSharedAnswerStream must be used inside AnswerStreamProvider");
  return context;
}
