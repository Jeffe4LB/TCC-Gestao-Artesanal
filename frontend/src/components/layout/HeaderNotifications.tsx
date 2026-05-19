import {
  BellOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
} from "@ant-design/icons";
import { App, Button, Divider, Empty, Popover, Spin, Typography, theme } from "antd";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import { useNotificationSummary } from "../../hooks/useNotificationSummary";
import { useNotifications } from "../../hooks/useNotifications";
import type { NotificationSummary, UserNotificationLevel } from "../../types/notifications";

function levelIcon(level: UserNotificationLevel, colorSuccess: string, colorError: string, colorWarning: string) {
  switch (level) {
    case "success":
      return <CheckCircleOutlined style={{ color: colorSuccess, fontSize: 16 }} />;
    case "error":
      return <CloseCircleOutlined style={{ color: colorError, fontSize: 16 }} />;
    case "warning":
      return <ExclamationCircleOutlined style={{ color: colorWarning, fontSize: 16 }} />;
    default:
      return <InfoCircleOutlined style={{ fontSize: 16, opacity: 0.75 }} />;
  }
}

function formatWhen(iso: string) {
  try {
    const d = new Date(iso);
    return d.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
  } catch {
    return iso;
  }
}

function formatMoneyBRL(value: string) {
  try {
    const n = Number(value);
    if (Number.isNaN(n)) return value;
    return n.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
  } catch {
    return value;
  }
}

function systemAttentionCount(
  summary: NotificationSummary | null,
  fallbackStock: number | null,
  fallbackFinance: number | null,
): number {
  if (summary) {
    const d = summary.finance.due_soon;
    return (
      summary.stock_below_minimum.count +
      summary.finance.overdue.payables_count +
      summary.finance.overdue.receivables_count +
      d.payables_count +
      d.receivables_count
    );
  }
  return (fallbackStock ?? 0) + (fallbackFinance ?? 0);
}

export type HeaderNotificationsProps = {
  stockAlertCount: number | null;
  financeOverdueCount: number | null;
};

export function HeaderNotifications({ stockAlertCount, financeOverdueCount }: HeaderNotificationsProps) {
  const { token } = theme.useToken();
  const { notification } = App.useApp();
  const { user } = useAuth();
  const cap = user?.capabilities;
  const summaryEnabled = Boolean(cap?.dashboard);
  const { summary, loading: summaryLoading } = useNotificationSummary(summaryEnabled);
  const { items, unreadCount, loading, markRead, markAllRead } = useNotifications();
  const [open, setOpen] = useState(false);
  const [markingAll, setMarkingAll] = useState(false);

  const systemCount = useMemo(
    () => systemAttentionCount(summary, stockAlertCount, financeOverdueCount),
    [summary, stockAlertCount, financeOverdueCount],
  );

  const badgeTotal = unreadCount + systemCount;
  const showSystemBlock = systemCount > 0;

  const systemSection = (() => {
    if (summaryLoading && !summary && summaryEnabled) {
      return (
        <div style={{ textAlign: "center", padding: "8px 0 12px" }}>
          <Spin size="small" />
        </div>
      );
    }

    if (!showSystemBlock) return null;

    if (summary) {
      const st = summary.stock_below_minimum;
      const ov = summary.finance.overdue;
      const ds = summary.finance.due_soon;
      return (
        <div style={{ marginBottom: 10 }}>
          <Typography.Text type="secondary" style={{ fontSize: 11, textTransform: "uppercase" }}>
            Alertas do sistema
          </Typography.Text>
          {cap?.stock_read && st.count > 0 ? (
            <div style={{ marginTop: 8 }}>
              <Link to="/app/estoque/alertas" style={{ fontWeight: 600, fontSize: 13 }}>
                Estoque abaixo do mínimo ({st.count})
              </Link>
              {st.preview.length ? (
                <ul style={{ margin: "6px 0 0", paddingLeft: 18, fontSize: 12, color: token.colorTextSecondary }}>
                  {st.preview.slice(0, 5).map((p) => (
                    <li key={p.sku}>
                      <Typography.Text ellipsis style={{ maxWidth: 260, display: "inline-block", verticalAlign: "bottom" }}>
                        {p.name} ({p.sku})
                      </Typography.Text>
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>
          ) : null}
          {cap?.finance && (ov.payables_count > 0 || ov.receivables_count > 0) ? (
            <div style={{ marginTop: 10 }}>
              <Link to="/app/financeiro/alertas" style={{ fontWeight: 600, fontSize: 13 }}>
                Títulos vencidos
              </Link>
              <Typography.Paragraph type="secondary" style={{ marginBottom: 0, marginTop: 4, fontSize: 12 }}>
                A pagar: {ov.payables_count} ({formatMoneyBRL(ov.payables_total)}) · A receber: {ov.receivables_count} (
                {formatMoneyBRL(ov.receivables_total)})
              </Typography.Paragraph>
            </div>
          ) : null}
          {cap?.finance && (ds.payables_count > 0 || ds.receivables_count > 0) ? (
            <div style={{ marginTop: 10 }}>
              <Link to="/app/financeiro/alertas" style={{ fontWeight: 600, fontSize: 13 }}>
                Vencendo em até {summary.finance.days_ahead} dias
              </Link>
              <Typography.Paragraph type="secondary" style={{ marginBottom: 0, marginTop: 4, fontSize: 12 }}>
                A pagar: {ds.payables_count} · A receber: {ds.receivables_count}
              </Typography.Paragraph>
            </div>
          ) : null}
        </div>
      );
    }

    return (
      <div style={{ marginBottom: 10 }}>
        <Typography.Text type="secondary" style={{ fontSize: 11, textTransform: "uppercase" }}>
          Alertas do sistema
        </Typography.Text>
        {cap?.stock_read && stockAlertCount != null && stockAlertCount > 0 ? (
          <div style={{ marginTop: 8 }}>
            <Link to="/app/estoque/alertas" style={{ fontWeight: 600, fontSize: 13 }}>
              Estoque abaixo do mínimo ({stockAlertCount})
            </Link>
          </div>
        ) : null}
        {cap?.finance && financeOverdueCount != null && financeOverdueCount > 0 ? (
          <div style={{ marginTop: 8 }}>
            <Link to="/app/financeiro/alertas" style={{ fontWeight: 600, fontSize: 13 }}>
              Títulos vencidos ({financeOverdueCount})
            </Link>
          </div>
        ) : null}
      </div>
    );
  })();

  const content = (
    <div
      style={{
        width: 320,
        maxWidth: "min(320px, 92vw)",
        maxHeight: 440,
        display: "flex",
        flexDirection: "column",
        padding: 4,
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 8,
          gap: 8,
        }}
      >
        <Typography.Text strong>Notificações</Typography.Text>
        <Button
          type="link"
          size="small"
          disabled={unreadCount === 0 || markingAll}
          loading={markingAll}
          onClick={async () => {
            setMarkingAll(true);
            try {
              await markAllRead();
              notification.success({
                message: "Todas marcadas como lidas",
                placement: "topRight",
              });
            } catch {
              notification.error({
                message: "Não foi possível marcar todas como lidas",
                placement: "topRight",
              });
            } finally {
              setMarkingAll(false);
            }
          }}
        >
          Marcar mensagens lidas
        </Button>
      </div>
     
      <div style={{ overflowY: "auto", flex: 1, minHeight: 0 }}>
        {systemSection}
        {showSystemBlock && items.length ? <Divider style={{ margin: "8px 0" }} /> : null}
        {!showSystemBlock && !items.length && loading && !summaryLoading ? (
          <div style={{ textAlign: "center", padding: 24 }}>
            <Spin size="small" />
          </div>
        ) : null}
        {!showSystemBlock && !items.length && !loading && !summaryLoading ? (
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Sem alertas nem mensagens" />
        ) : null}
        {items.length ? (
          <Typography.Text type="secondary" style={{ fontSize: 11, textTransform: "uppercase", display: "block", marginBottom: 6 }}>
            Mensagens
          </Typography.Text>
        ) : null}
        {items.map((n) => (
          <button
            type="button"
            key={n.id}
            onClick={() => {
              if (!n.read_at) void markRead(n.id);
            }}
            style={{
              width: "100%",
              textAlign: "left",
              border: "none",
              background: n.read_at ? "transparent" : token.colorFillAlter,
              borderRadius: token.borderRadius,
              padding: "8px 10px",
              marginBottom: 6,
              cursor: n.read_at ? "default" : "pointer",
              display: "flex",
              gap: 10,
              alignItems: "flex-start",
              borderLeft: `3px solid ${
                n.level === "success"
                  ? token.colorSuccess
                  : n.level === "error"
                    ? token.colorError
                    : n.level === "warning"
                      ? token.colorWarning
                      : token.colorInfo
              }`,
            }}
          >
            <span style={{ marginTop: 2 }} aria-hidden>
              {levelIcon(n.level, token.colorSuccess, token.colorError, token.colorWarning)}
            </span>
            <span style={{ minWidth: 0, flex: 1 }}>
              <Typography.Text strong style={{ display: "block", fontSize: 13 }}>
                {n.title}
              </Typography.Text>
              {n.body ? (
                <Typography.Paragraph
                  type="secondary"
                  ellipsis={{ rows: 2 }}
                  style={{ marginBottom: 4, fontSize: 12 }}
                >
                  {n.body}
                </Typography.Paragraph>
              ) : null}
              <Typography.Text type="secondary" style={{ fontSize: 11 }}>
                {formatWhen(n.created_at)}
                {n.read_at ? " · Lida" : ""}
              </Typography.Text>
            </span>
          </button>
        ))}
      </div>
    </div>
  );

  return (
    <Popover
      open={open}
      onOpenChange={setOpen}
      trigger="click"
      placement="bottomRight"
      content={content}
    >
      <Button
        type="text"
        aria-label={`Notificações${badgeTotal ? `, ${badgeTotal} em atenção` : ""}`}
        icon={
          <span className="header-notifications-bell-wrap">
            <BellOutlined style={{ fontSize: 18 }} />
            {badgeTotal > 0 ? (
              <span className="header-notifications-badge">{badgeTotal > 99 ? "99+" : badgeTotal}</span>
            ) : null}
          </span>
        }
      />
    </Popover>
  );
}
