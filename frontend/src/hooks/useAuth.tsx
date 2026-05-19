import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { clearTokens, getAccessToken, login as sessionLogin } from "../api/session";
import { AUTH_TOKENS_CLEARED_EVENT } from "../constants/authEvents";
import { fetchMe } from "../api/user";
import type { MeUser } from "../types/auth";

type AuthContextValue = {
  user: MeUser | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<MeUser | null>(null);
  const [loading, setLoading] = useState(true);

  const bootstrap = useCallback(async () => {
    if (!getAccessToken()) {
      setLoading(false);
      return;
    }
    try {
      const me = await fetchMe();
      setUser(me);
    } catch {
      clearTokens();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void bootstrap();
  }, [bootstrap]);

  useEffect(() => {
    const onTokensCleared = () => {
      setUser(null);
    };
    window.addEventListener(AUTH_TOKENS_CLEARED_EVENT, onTokensCleared);
    return () => window.removeEventListener(AUTH_TOKENS_CLEARED_EVENT, onTokensCleared);
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    await sessionLogin(username, password);
    const me = await fetchMe();
    setUser(me);
  }, []);

  const logout = useCallback(() => {
    clearTokens();
    setUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
    if (!getAccessToken()) return;
    try {
      const me = await fetchMe();
      setUser(me);
    } catch {
      clearTokens();
      setUser(null);
    }
  }, []);

  const value = useMemo(
    () => ({
      user,
      loading,
      isAuthenticated: !!user,
      login,
      logout,
      refreshUser,
    }),
    [user, loading, login, logout, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth deve ser usado dentro de AuthProvider");
  }
  return ctx;
}
