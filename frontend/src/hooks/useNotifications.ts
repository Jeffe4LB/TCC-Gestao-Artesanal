import { useCallback, useEffect, useRef, useState } from "react";
import {
  listUserNotifications,
  markAllUserNotificationsRead,
  markUserNotificationRead,
} from "../api/notifications";
import { getAccessToken } from "../api/session";
import { NOTIFICATIONS_REFRESH_EVENT } from "../constants/notificationsEvents";
import type { UserNotificationRow } from "../types/notifications";

export function useNotifications(pollIntervalMs = 45_000) {
  const [items, setItems] = useState<UserNotificationRow[]>([]);
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
        listUserNotifications({ page: 1, pageSize: 15 }),
        listUserNotifications({ page: 1, pageSize: 1, unread: true }),
      ]);
      setItems(recent.results);
      setUnreadCount(unreadPage.count);
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
    window.addEventListener(NOTIFICATIONS_REFRESH_EVENT, onCustom);
    return () => {
      window.clearInterval(t);
      window.removeEventListener("focus", onFocus);
      window.removeEventListener(NOTIFICATIONS_REFRESH_EVENT, onCustom);
    };
  }, [refresh, pollIntervalMs]);

  const markRead = useCallback(
    async (id: number) => {
      if (!getAccessToken()) return;
      try {
        await markUserNotificationRead(id);
        await refresh();
      } catch {
        /* ignorar */
      }
    },
    [refresh],
  );

  const markAllRead = useCallback(async () => {
    if (!getAccessToken()) return;
    await markAllUserNotificationsRead();
    await refresh();
  }, [refresh]);

  return { items, unreadCount, loading, refresh, markRead, markAllRead };
}
