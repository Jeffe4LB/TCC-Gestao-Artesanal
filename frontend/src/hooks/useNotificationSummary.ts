import { useCallback, useEffect, useRef, useState } from "react";
import { fetchNotificationSummary } from "../api/notifications";
import { getAccessToken } from "../api/session";
import { NOTIFICATIONS_REFRESH_EVENT } from "../constants/notificationsEvents";
import type { NotificationSummary } from "../types/notifications";

const POLL_MS = 60_000;

/** Resumo de alertas (mesmo endpoint do dashboard); exige capability `dashboard`. */
export function useNotificationSummary(enabled: boolean) {
  const [summary, setSummary] = useState<NotificationSummary | null>(null);
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
      const s = await fetchNotificationSummary(7, 8);
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
    window.addEventListener(NOTIFICATIONS_REFRESH_EVENT, onCustom);
    return () => {
      window.clearInterval(t);
      window.removeEventListener("focus", onFocus);
      window.removeEventListener(NOTIFICATIONS_REFRESH_EVENT, onCustom);
    };
  }, [enabled, refresh]);

  return { summary, loading, refresh };
}
