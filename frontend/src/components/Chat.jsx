import { useEffect, useRef, useState } from "react";
import { Send, Sparkles, Loader2 } from "lucide-react";
import { getToken, getUser } from "../utils/auth";
import { MessageBubble } from "./MessageBubble";
import { ErrorCard } from "./ErrorCard";
import { SourceCard } from "./SourceCard";

const ROLE_CONFIG = {
  admin: {
    title: "Admin intelligence",
    subtitle: "System-wide visibility",
    placeholder: "Ask about system configuration, audit trails, or global policies",
    accent: "from-indigo-500 to-violet-500"
  },
  hr: {
    title: "HR intelligence",
    subtitle: "Policies and people operations",
    placeholder: "Ask about leave, benefits, onboarding or performance reviews",
    accent: "from-sky-500 to-cyan-500"
  },
  manager: {
    title: "Manager intelligence",
    subtitle: "Decision and team support",
    placeholder: "Ask about approvals, team policies or performance expectations",
    accent: "from-emerald-500 to-teal-500"
  },
  employee: {
    title: "Employee assistant",
    subtitle: "Everyday guidance",
    placeholder: "Ask about company policies, expenses, or remote work",
    accent: "from-blue-500 to-indigo-500"
  }
};

export function Chat({ sessions, currentSessionId, onSessionsChange, onSessionChange }) {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sources, setSources] = useState([]);
  const messagesEndRef = useRef(null);
  const user = getUser();
  const roleKey = user?.role || "employee";
  const role = ROLE_CONFIG[roleKey] || ROLE_CONFIG.employee;

  useEffect(() => {
    if (!currentSessionId) {
      setMessages([]);
      setSources([]);
      setError(null);
      return;
    }
    const token = getToken();
    if (!token) {
      return;
    }
    const fetchSession = async () => {
      try {
        const res = await fetch(`/api/v1/chat/sessions/${currentSessionId}`, {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });
        if (!res.ok) {
          return;
        }
        const data = await res.json();
        setMessages(data.messages || []);
        setSources([]);
        setError(null);
      } catch {
        setError({
          type: "network",
          message: "Failed to load conversation."
        });
      }
    };
    fetchSession();
  }, [currentSessionId]);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, loading]);

  const handleSubmit = async (e) => {
    if (e) {
      e.preventDefault();
    }
    const trimmed = input.trim();
    if (!trimmed || loading) {
      return;
    }
    setInput("");
    setError(null);
    setSources([]);
    const nextMessages = [...messages, { role: "user", content: trimmed }];
    setMessages(nextMessages);
    setLoading(true);
    const token = getToken();
    try {
      const res = await fetch("/api/v1/chat/stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          message: trimmed,
          session_id: currentSessionId || null
        })
      });
      if (!res.ok || !res.body) {
        throw new Error(`Request failed with status ${res.status}`);
      }
      let text = "";
      setMessages((prev) => [...prev, { role: "assistant", content: "" }]);
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      for (;;) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() || "";
        for (const raw of parts) {
          const line = raw.trim();
          if (!line.startsWith("data:")) {
            continue;
          }
          const payload = line.slice(5).trim();
          if (!payload) {
            continue;
          }
          let data;
          try {
            data = JSON.parse(payload);
          } catch {
            continue;
          }
          if (data.type === "content") {
            text += data.content || "";
            setMessages((prev) => {
              const copy = [...prev];
              copy[copy.length - 1] = { role: "assistant", content: text };
              return copy;
            });
          }
          if (data.type === "sources") {
            setSources(data.sources || []);
          }
          if (data.type === "error") {
            setError({
              type: data.error_type || "general",
              message: data.error_message || "Something went wrong while generating a response."
            });
          }
        }
      }
      if (!currentSessionId) {
        const list = await fetch("/api/v1/chat/sessions", {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });
        if (list.ok) {
          const items = await list.json();
          onSessionsChange(items);
          if (items.length > 0) {
            onSessionChange(items[0].id);
          }
        }
      } else {
        const list = await fetch("/api/v1/chat/sessions", {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });
        if (list.ok) {
          const items = await list.json();
          onSessionsChange(items);
        }
      }
    } catch (err) {
      setError({
        type: "network",
        message: err.message || "Network error while streaming the response."
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-full flex-1 flex-col">
      <header className="flex items-center justify-between border-b border-slate-200 bg-white px-5 py-3">
        <div>
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
            <span className={`flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br ${role.accent} text-white`}>
              <Sparkles size={15} />
            </span>
            <span>{role.title}</span>
          </div>
          <div className="text-xs text-slate-500">
            {role.subtitle}
          </div>
        </div>
        {user && (
          <div className="flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700">
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            <span>{user.full_name || user.username}</span>
            <span className="text-[10px] uppercase tracking-wide text-slate-500">
              {user.role}
            </span>
          </div>
        )}
      </header>
      <main className="flex-1 overflow-y-auto bg-slate-50 px-4 py-4">
        {messages.length === 0 && !loading && (
          <div className="mx-auto flex max-w-xl flex-col items-center gap-3 rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-8 text-center">
            <div className={`flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br ${role.accent} text-white`}>
              <Sparkles size={22} />
            </div>
            <div className="text-sm font-semibold text-slate-900">
              How can I help you today?
            </div>
            <div className="text-xs text-slate-500">
              Ask about HR policies, procedures, approvals or any internal knowledge in your company.
            </div>
          </div>
        )}
        <div className="space-y-3">
          {messages.map((m, index) => (
            <MessageBubble key={index} role={m.role} content={m.content} />
          ))}
          {loading && (
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <Loader2 size={14} className="animate-spin" />
              <span>Generating answer</span>
            </div>
          )}
          {error && (
            <ErrorCard
              type={error.type}
              message={error.message}
              onRetry={() => {
                setError(null);
              }}
            />
          )}
          {sources.length > 0 && (
            <div className="mt-4 space-y-1 rounded-xl border border-slate-200 bg-white px-3 py-2">
              <div className="text-xs font-semibold text-slate-700">
                Sources
              </div>
              <div className="grid gap-2 md:grid-cols-2">
                {sources.map((s, index) => (
                  <SourceCard key={index} source={s} />
                ))}
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </main>
      <form onSubmit={handleSubmit} className="border-t border-slate-200 bg-white px-4 py-3">
        <div className="mx-auto flex max-w-3xl items-end gap-2 rounded-2xl border border-slate-300 bg-slate-50 px-3 py-2 focus-within:border-indigo-500 focus-within:ring-1 focus-within:ring-indigo-500">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            rows={1}
            placeholder={role.placeholder}
            className="max-h-32 flex-1 resize-none bg-transparent text-sm text-slate-900 outline-none placeholder:text-slate-400"
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSubmit();
              }
            }}
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-indigo-600 text-white disabled:bg-slate-300"
          >
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
          </button>
        </div>
        <div className="mx-auto mt-1 max-w-3xl text-[10px] text-slate-400">
          Enter to send, Shift+Enter for new line
        </div>
      </form>
    </div>
  );
}
