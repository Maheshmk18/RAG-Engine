export function SourceCard({ source }) {
  const label = source.filename || `Document ${source.document_id || ""}`.trim();
  const index = typeof source.chunk_index === "number" ? source.chunk_index + 1 : null;
  const score = typeof source.score === "number" ? source.score : null;

  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-700">
      <div className="flex items-center justify-between gap-2">
        <div className="font-medium truncate">{label}</div>
        {score !== null && (
          <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-700">
            score {score.toFixed(2)}
          </span>
        )}
      </div>
      {index !== null && (
        <div className="mt-1 text-[11px] text-slate-500">
          chunk {index}
        </div>
      )}
    </div>
  );
}
