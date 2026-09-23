import { createContext, useContext } from "react";
import type { User } from "./types";

export interface AuthState {
  user: User | null;
  status: "loading" | "signed-in" | "signed-out";
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => void;
  replaceUser: (user: User) => void;
}

export const AuthContext = createContext<AuthState | null>(null);

export function useAuth(): AuthState {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}

export function useCurrentUser(): User {
  const { user } = useAuth();
  if (!user) throw new Error("useCurrentUser requires a signed-in user");
  return user;
}
