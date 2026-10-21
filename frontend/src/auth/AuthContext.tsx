import { useQueryClient } from "@tanstack/react-query";
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { api, getTokens, handleSessionExpired, setTokens } from "../api/client";
import type { Role, User } from "../api/types";

type Status = "loading" | "signed-out" | "signed-in";

interface RegisterInput {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  role: Exclude<Role, "admin">;
}

interface AuthValue {
  user: User | null;
  status: Status;
  logIn: (email: string, password: string) => Promise<User>;
  register: (input: RegisterInput) => Promise<User>;
  logOut: () => void;
}

const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<Status>(() => (getTokens() ? "loading" : "signed-out"));

  const loadMe = useCallback(async () => {
    const me = await api<User>("/api/users/me/");
    setUser(me);
    setStatus("signed-in");
    return me;
  }, []);

  const logOut = useCallback(() => {
    setTokens(null);
    setUser(null);
    setStatus("signed-out");
    queryClient.clear();
  }, [queryClient]);

  useEffect(() => {
    handleSessionExpired(logOut);
    if (getTokens()) loadMe().catch(logOut);
  }, [loadMe, logOut]);

  const logIn = useCallback(
    async (email: string, password: string) => {
      const tokens = await api<{ access: string; refresh: string }>("/api/auth/login/", {
        method: "POST",
        body: { email, password },
      });
      setTokens(tokens);
      queryClient.clear();
      return loadMe();
    },
    [loadMe, queryClient],
  );

  const register = useCallback(
    async (input: RegisterInput) => {
      await api("/api/auth/register/", { method: "POST", body: { ...input } });
      return logIn(input.email, input.password);
    },
    [logIn],
  );

  const value = useMemo(() => ({ user, status, logIn, register, logOut }), [user, status, logIn, register, logOut]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside <AuthProvider>");
  return value;
}
