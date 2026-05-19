import type {
  NotificationSummary,
  PaginatedUserNotifications,
  UserNotificationLevel,
  UserNotificationRow,
} from "../types/notifications";
import { apiGet, apiPost } from "./client";

export type {
  NotificationSummary,
  PaginatedUserNotifications,
  UserNotificationLevel,
  UserNotificationRow,
} from "../types/notifications";

export function fetchNotificationSummary(
  daysAhead = 7,
  stockPreview = 10,
  from?: string,
  to?: string,
): Promise<NotificationSummary> {
  const q = new URLSearchParams({
    days_ahead: String(daysAhead),
    stock_preview: String(stockPreview),
  });
  if (from) q.set("from", from);
  if (to) q.set("to", to);
  return apiGet<NotificationSummary>(`/notifications/summary/?${q}`);
}

export function listUserNotifications(params: {
  page?: number;
  pageSize?: number;
  unread?: boolean;
}): Promise<PaginatedUserNotifications> {
  const q = new URLSearchParams();
  if (params.page != null) q.set("page", String(params.page));
  if (params.pageSize != null) q.set("page_size", String(params.pageSize));
  if (params.unread) q.set("unread", "1");
  const suffix = q.toString() ? `?${q}` : "";
  return apiGet<PaginatedUserNotifications>(`/notifications/${suffix}`);
}

export function createUserNotification(payload: {
  level: UserNotificationLevel;
  title: string;
  body?: string;
}): Promise<UserNotificationRow> {
  return apiPost<UserNotificationRow>("/notifications/", {
    level: payload.level,
    title: payload.title,
    body: payload.body ?? "",
  });
}

export function markUserNotificationRead(id: number): Promise<UserNotificationRow> {
  return apiPost<UserNotificationRow>(`/notifications/${id}/read/`);
}

export function markAllUserNotificationsRead(): Promise<{ detail: string }> {
  return apiPost<{ detail: string }>("/notifications/read-all/");
}
