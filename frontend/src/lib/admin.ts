import { useCallback, useSyncExternalStore } from "react";
import { adminKey, api } from "./api";

const listeners = new Set<() => void>();

function notify() {
  for (const listener of listeners) listener();
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function unlockedSnapshot() {
  return adminKey.get() !== null;
}

export function useAdminAccess() {
  const unlocked = useSyncExternalStore(subscribe, unlockedSnapshot, () => false);

  const unlock = useCallback(async (key: string) => {
    await api.verifyAdminKey(key);
    adminKey.set(key);
    notify();
  }, []);

  const lock = useCallback(() => {
    adminKey.set(null);
    notify();
  }, []);

  return { unlocked, unlock, lock };
}
