export type UserNotificationLevel = "success" | "error" | "info" | "warning";

export type UserNotificationRow = {
  id: number;
  level: UserNotificationLevel;
  title: string;
  body: string;
  read_at: string | null;
  created_at: string;
};

export type PaginatedUserNotifications = {
  count: number;
  next: string | null;
  previous: string | null;
  results: UserNotificationRow[];
};

export type NotificationSummary = {
  generated_at: string;
  stock_below_minimum: {
    count: number;
    preview: Array<{
      sku: string;
      name: string;
      min_stock: string;
      current_quantity: string;
      gap: string;
    }>;
  };
  finance: {
    today: string;
    until: string;
    days_ahead: number;
    overdue: {
      payables_count: number;
      payables_total: string;
      receivables_count: number;
      receivables_total: string;
    };
    due_soon: {
      payables_count: number;
      receivables_count: number;
    };
  };
};
