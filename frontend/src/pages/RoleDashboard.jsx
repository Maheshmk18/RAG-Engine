import { getUser } from "../utils/auth";

export function RoleDashboardPage() {
  const user = getUser();
  const label =
    user?.role === "hr"
      ? "HR dashboard"
      : user?.role === "manager"
      ? "Manager dashboard"
      : "Employee dashboard";

  return (
    <div className="flex h-screen flex-col bg-slate-950 text-slate-50">
      <header className="border-b border-slate-800 px-6 py-3 text-sm font-semibold">
        {label}
      </header>
      <main className="flex-1 px-6 py-4">
        <div className="text-xs text-slate-400">
          This space is reserved for role-specific metrics and quick links you can extend later.
        </div>
      </main>
    </div>
  );
}

