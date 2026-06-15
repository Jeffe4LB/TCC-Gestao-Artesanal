import { useCallback, useEffect, useRef, useState } from "react";
import {
  listarNotificacoesUsuario,
  marcarNotificacaoLida,
  marcarTodasNotificacoesLidas,
} from "../api/notificacoes";
import { getAccessToken } from "../api/sessao";
import { EVENTO_ATUALIZAR_NOTIFICACOES } from "../constants/eventosNotificacoes";
import type { LinhaNotificacaoUsuario } from "../types/notificacoes";

export function useNotificacoes(pollIntervalMs = 45_000) {
  const [items, setItems] = useState<LinhaNotificacaoUsuario[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const refreshInFlight = useRef(false);

  const refresh = useCallback(async () => {
    if (!getAccessToken()) {
      setItems([]);
      setUnreadCount(0);
      setLoading(false);
      return;
    }
    if (refreshInFlight.current) return;
    refreshInFlight.current = true;
    setLoading(true);
    try {
      const [recent, unreadPage] = await Promise.all([
        listarNotificacoesUsuario({ page: 1, pageSize: 15 }),
        listarNotificacoesUsuario({ page: 1, pageSize: 1, unread: true }),
      ]);
      setItems(recent.resultados);
      setUnreadCount(unreadPage.total);
    } catch {
      /* silencioso no header */
    } finally {
      refreshInFlight.current = false;
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    const t = window.setInterval(() => void refresh(), pollIntervalMs);
    const onFocus = () => void refresh();
    const onCustom = () => void refresh();
    window.addEventListener("focus", onFocus);
    window.addEventListener(EVENTO_ATUALIZAR_NOTIFICACOES, onCustom);
    return () => {
      window.clearInterval(t);
      window.removeEventListener("focus", onFocus);
      window.removeEventListener(EVENTO_ATUALIZAR_NOTIFICACOES, onCustom);
    };
  }, [refresh, pollIntervalMs]);

  const markRead = useCallback(
    async (id: number) => {
      if (!getAccessToken()) return;
      try {
        await marcarNotificacaoLida(id);
        await refresh();
      } catch {
        /* ignorar */
      }
    },
    [refresh],
  );

  const markAllRead = useCallback(async () => {
    if (!getAccessToken()) return;
    await marcarTodasNotificacoesLidas();
    await refresh();
  }, [refresh]);

  return { items, unreadCount, loading, refresh, markRead, markAllRead };
}
