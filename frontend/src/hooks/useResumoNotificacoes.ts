import { useCallback, useEffect, useRef, useState } from "react";
import { buscarResumoNotificacoes } from "../api/notificacoes";
import { getAccessToken } from "../api/sessao";
import { EVENTO_ATUALIZAR_NOTIFICACOES } from "../constants/eventosNotificacoes";
import type { ResumoNotificacoes } from "../types/notificacoes";

const POLL_MS = 60_000;

/** Resumo de alertas (mesmo endpoint do dashboard); exige capacidade `painel`. */
export function useResumoNotificacoes(enabled: boolean) {
  const [summary, setSummary] = useState<ResumoNotificacoes | null>(null);
  const [loading, setLoading] = useState(false);
  const inFlight = useRef(false);

  const refresh = useCallback(async () => {
    if (!enabled || !getAccessToken()) {
      setSummary(null);
      setLoading(false);
      return;
    }
    if (inFlight.current) return;
    inFlight.current = true;
    setLoading(true);
    try {
      const s = await buscarResumoNotificacoes(7, 8);
      setSummary(s);
    } catch {
      setSummary(null);
    } finally {
      inFlight.current = false;
      setLoading(false);
    }
  }, [enabled]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    if (!enabled) return;
    const t = window.setInterval(() => void refresh(), POLL_MS);
    const onFocus = () => void refresh();
    const onCustom = () => void refresh();
    window.addEventListener("focus", onFocus);
    window.addEventListener(EVENTO_ATUALIZAR_NOTIFICACOES, onCustom);
    return () => {
      window.clearInterval(t);
      window.removeEventListener("focus", onFocus);
      window.removeEventListener(EVENTO_ATUALIZAR_NOTIFICACOES, onCustom);
    };
  }, [enabled, refresh]);

  return { summary, loading, refresh };
}
