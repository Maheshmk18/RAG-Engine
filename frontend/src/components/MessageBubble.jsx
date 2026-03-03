import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export function MessageBubble({ role, content }) {
  const isUser = role === "user";

  return (
    <div className={`flex gap-2 ${isUser ? "flex-row-reverse" : ""}`}>
      <div
        className={`flex h-8 w-8 items-center justify-center rounded-lg text-xs font-semibold ${
          isUser ? "bg-slate-900 text-white" : "bg-indigo-100 text-indigo-700"
        }`}
      >
        {isUser ? "You" : "AI"}
      </div>
      <div className={`max-w-xl rounded-2xl px-3 py-2 text-sm leading-relaxed ${isUser ? "bg-slate-900 text-slate-50" : "bg-white text-slate-900 border border-slate-200"}`}>
        {isUser ? (
          <p className="whitespace-pre-wrap">{content}</p>
        ) : (
          <ReactMarkdown remarkPlugins={[remarkGfm]} className="prose prose-sm max-w-none">
            {content}
          </ReactMarkdown>
        )}
      </div>
    </div>
  );
}

