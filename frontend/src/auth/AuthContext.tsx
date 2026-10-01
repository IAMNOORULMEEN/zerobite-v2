import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import api, {
  clearTokens,
  getRefreshToken,
  refreshAccessToken,
  setAccessToken,
  setRefreshToken,
} from "../lib/api";
import type { LoginResponse, RegisterPayload, User } from "../types/auth";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<User>;
  register: (payload: RegisterPayload) => Promise<User>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<User | null>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchMe = useCallback(async (): Promise<User | null> => {
    const { data } = await api.get<User>("/auth/me/");
    setUser(data);
    return data;
  }, []);

  const refreshUser = useCallback(async (): Promise<User | null> => {
    try {
      return await fetchMe();
    } catch {
      return null;
    }
  }, [fetchMe]);

  // Restore session on app load.
  useEffect(() => {
    let cancelled = false;

    async function restore() {
      const refresh = getRefreshToken();
      if (!refresh) {
        if (!cancelled) setLoading(false);
        return;
      }
      try {
        await refreshAccessToken();
        if (!cancelled) await fetchMe();
      } catch {
        clearTokens();
        if (!cancelled) setUser(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void restore();
    return () => {
      cancelled = true;
    };
  }, [fetchMe]);

  const login = useCallback(
    async (email: string, password: string): Promise<User> => {
      const { data } = await api.post<LoginResponse>("/auth/login/", {
        email,
        password,
      });
      setAccessToken(data.access);
      setRefreshToken(data.refresh);
      return (await fetchMe()) as User;
    },
    [fetchMe],
  );

  const register = useCallback(
    async (payload: RegisterPayload): Promise<User> => {
      // Registration is public; the backend returns the created user only.
      const { data } = await api.post<User>("/auth/register/", payload);
      return data;
    },
    [],
  );

  const logout = useCallback(async (): Promise<void> => {
    const refresh = getRefreshToken();
    try {
      if (refresh) {
        await api.post("/auth/logout/", { refresh });
      }
    } catch {
      // Intentionally swallow: clearing local state is what matters.
    } finally {
      clearTokens();
      setUser(null);
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ user, loading, login, register, logout, refreshUser }),
    [user, loading, login, register, logout, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used inside <AuthProvider>.");
  }
  return ctx;
}
