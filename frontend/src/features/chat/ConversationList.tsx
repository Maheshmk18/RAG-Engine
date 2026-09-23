import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Trash2 } from "lucide-react";
import { NavLink, useNavigate, useParams } from "react-router";
import { IconButton } from "@/components/ui/Button";
import { api } from "@/lib/api";
import { dayBucket } from "@/lib/format";
import type { Bucket } from "@/lib/format";
import type { Session } from "@/lib/types";
import styles from "./ConversationList.module.css";

const ORDER: Bucket[] = ["Today", "Yesterday", "Previous 7 days", "Older"];

export function ConversationList({ sessions, loading }: { sessions: Session[]; loading: boolean }) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { sessionId } = useParams();

  const remove = useMutation({
    mutationFn: api.deleteSession,
    onSuccess: (_, id) => {
      queryClient.setQueryData<Session[]>(["sessions"], (current) =>
        current?.filter((item) => item.id !== id),
      );
      queryClient.removeQueries({ queryKey: ["session", id] });
      if (id === sessionId) navigate("/chat");
    },
  });

  const groups = ORDER.map((bucket) => ({
    bucket,
    items: sessions.filter((item) => dayBucket(item.updated_at) === bucket),
  })).filter((group) => group.items.length > 0);

  return (
    <div className={styles.list}>
      {!loading && sessions.length === 0 && (
        <p className={styles.empty}>Your conversations will appear here.</p>
      )}
      {groups.map((group) => (
        <section key={group.bucket} aria-label={group.bucket}>
          <h3 className={styles.heading}>{group.bucket}</h3>
          <ul>
            {group.items.map((item) => (
              <li key={item.id} className={styles.row}>
                <NavLink
                  to={`/chat/${item.id}`}
                  className={({ isActive }) => `${styles.link} ${isActive ? styles.active : ""}`}
                  title={item.title}
                >
                  {item.title}
                </NavLink>
                <IconButton
                  label={`Delete "${item.title}"`}
                  className={styles.delete}
                  onClick={() => {
                    if (window.confirm(`Delete "${item.title}"? This cannot be undone.`)) {
                      remove.mutate(item.id);
                    }
                  }}
                >
                  <Trash2 size={14} />
                </IconButton>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
