import { useEffect, useState } from "react";
import { getToken } from "../utils/auth";

export function AdminUsersPage() {
  const [users, setUsers] = useState([]);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      return;
    }
    const load = async () => {
      const res = await fetch("/api/v1/users", {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      if (!res.ok) {
        return;
      }
      const data = await res.json();
      setUsers(data);
    };
    load();
  }, []);

  return (
    <div className="flex h-screen flex-col bg-slate-950 text-slate-50">
      <header className="border-b border-slate-800 px-6 py-3 text-sm font-semibold">
        User management
      </header>
      <main className="flex-1 px-6 py-4">
        <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900">
          <table className="min-w-full text-left text-xs text-slate-200">
            <thead className="bg-slate-900/80 text-[11px] uppercase tracking-wide text-slate-400">
              <tr>
                <th className="px-3 py-2">ID</th>
                <th className="px-3 py-2">Username</th>
                <th className="px-3 py-2">Email</th>
                <th className="px-3 py-2">Role</th>
                <th className="px-3 py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-t border-slate-800/70">
                  <td className="px-3 py-2 text-slate-400">{u.id}</td>
                  <td className="px-3 py-2">{u.username}</td>
                  <td className="px-3 py-2 text-slate-300">{u.email}</td>
                  <td className="px-3 py-2 text-slate-300">{u.role}</td>
                  <td className="px-3 py-2 text-slate-300">
                    {u.is_active ? "Active" : "Inactive"}
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-3 py-4 text-center text-slate-500">
                    No users yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}

