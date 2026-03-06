import { AlertTriangle } from "lucide-react";

export function ErrorCard({ type, message, onRetry }) {
  const title =
    type === "quota"
      ? "AI quota exceeded"
      : type === "network"
      ? "Network issue"
      : type === "auth"
      ? "Authentication problem"
      : "Something went wrong";

  return (
    <div className="flex gap-3 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-800 shadow-sm max-w-md">
      <div className="flex h-8 w-8 items-center justify-center rounded-md bg-red-100 text-red-600">
        <AlertTriangle size={16} />
      </div>
      <div className="flex-1">
        <div className="font-semibold">{title}</div>
        <div className="mt-1 text-xs leading-relaxed">{message}</div>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="mt-2 inline-flex items-center rounded-md border border-red-300 px-2.5 py-1 text-xs font-medium text-red-700 hover:bg-red-100"
          >
            Try again
          </button>
        )}
      </div>
    </div>
  );
}
