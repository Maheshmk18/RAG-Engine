import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { api, session } from "./api";
import { AuthContext } from "./authContext";
import type { AuthState } from "./authContext";
import type { User } from "./types";

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<AuthState["status"]>(() =>
    session.token() ? "loading" : "signed-out",
  );

  const signOut = useCallback(() => {
    session.clear();
    queryClient.clear();
    setUser(null);
    setStatus("signed-out");
  }, [queryClient]);

  useEffect(() => {
    session.onUnauthorized(signOut);
    if (!session.token()) return;
    api
      .me()
      .then((profile) => {
        setUser(profile);
        setStatus("signed-in");
      })
      .catch(signOut);
  }, [signOut]);

  const signIn = useCallback(async (email: string, password: string) => {
    const response = await api.login(email, password);
    session.store(response.access_token);
    setUser(response.user);
    setStatus("signed-in");
  }, []);

  const value = useMemo(
    () => ({ user, status, signIn, signOut, replaceUser: setUser }),
    [user, status, signIn, signOut],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
