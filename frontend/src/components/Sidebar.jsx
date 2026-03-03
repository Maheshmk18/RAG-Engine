import { Plus, MessageSquare, Trash2 } from "lucide-react";

export function Sidebar({ sessions, currentSessionId, onNew, onSelect, onDelete }) {
  return (
    <aside className="flex h-full w-64 flex-col border-r border-slate-200 bg-slate-950 text-slate-100">
      <div className="flex items-center justify-between px-4 py-3">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wide text-slate-400">
            Enterprise RAG
          </div>
          <div className="text-[11px] text-slate-500">
            Knowledge assistant
          </div>
        </div>
        <button
          type="button"
          onClick={onNew}
          className="inline-flex h-8 items-center gap-1 rounded-md bg-indigo-500 px-2.5 text-xs font-medium text-white hover:bg-indigo-400"
        >
          <Plus size={14} />
          New
        </button>
      </div>
      <div className="px-3 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
        Sessions
      </div>
      <div className="mt-1 flex-1 space-y-1 overflow-y-auto px-2 pb-3">
        {sessions.length === 0 && (
          <div className="px-2 py-3 text-xs text-slate-500">
            No conversations yet.
          </div>
        )}
        {sessions.map((s) => (
          <button
            key={s.id}
            type="button"
            onClick={() => onSelect(s.id)}
            className={`group flex w-full items-center justify-between rounded-md px-2.5 py-2 text-left text-xs ${
              currentSessionId === s.id
                ? "bg-slate-800 text-slate-50"
                : "text-slate-300 hover:bg-slate-900"
            }`}
          >
            <span className="flex min-w-0 items-center gap-2">
              <span className="flex h-6 w-6 items-center justify-center rounded-md bg-slate-900 text-slate-300">
                <MessageSquare size={13} />
              </span>
              <span className="truncate">{s.title}</span>
            </span>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onDelete(s.id);
              }}
              className="ml-2 inline-flex h-6 w-6 items-center justify-center rounded-md text-slate-500 hover:bg-slate-800 hover:text-red-400"
            >
              <Trash2 size={13} />
            </button>
          </button>
        ))}
      </div>
    </aside>
  );
}

