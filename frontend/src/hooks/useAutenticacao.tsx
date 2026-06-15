import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { clearTokens, getAccessToken, login as sessionLogin } from "../api/sessao";
import { AUTH_TOKENS_CLEARED_EVENT } from "../constants/eventosAutenticacao";
import { buscarSessao } from "../api/usuario";
import type { UsuarioSessao } from "../types/autenticacao";

type AuthContextValue = {
  user: UsuarioSessao | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<UsuarioSessao>;
  logout: () => void;
  refreshUser: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function ProvedorAutenticacao({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UsuarioSessao | null>(null);
  const [loading, setLoading] = useState(true);

  const bootstrap = useCallback(async () => {
    if (!getAccessToken()) {
      setLoading(false);
      return;
    }
    try {
      const me = await buscarSessao();
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
    const me = await buscarSessao();
    setUser(me);
    return me;
  }, []);

  const logout = useCallback(() => {
    clearTokens();
    setUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
    if (!getAccessToken()) return;
    try {
      const me = await buscarSessao();
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

export function useAutenticacao(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAutenticacao deve ser usado dentro de ProvedorAutenticacao");
  }
  return ctx;
}
