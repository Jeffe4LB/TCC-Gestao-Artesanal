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
import { useAutenticacao } from "../../hooks/useAutenticacao";
import { useResumoNotificacoes } from "../../hooks/useResumoNotificacoes";
import { useNotificacoes } from "../../hooks/useNotificacoes";
import type { NivelNotificacao, ResumoNotificacoes } from "../../types/notificacoes";

function levelIcon(nivel: NivelNotificacao, colorSuccess: string, colorError: string, colorWarning: string) {
  switch (nivel) {
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
  summary: ResumoNotificacoes | null,
  fallbackStock: number | null,
  fallbackFinance: number | null,
): number {
  if (summary) {
    const d = summary.financeiro.a_vencer;
    return (
      summary.estoque_abaixo_minimo.quantidade +
      summary.financeiro.vencidos.contagem_pagar +
      summary.financeiro.vencidos.contagem_receber +
      d.contagem_pagar +
      d.contagem_receber
    );
  }
  return (fallbackStock ?? 0) + (fallbackFinance ?? 0);
}

export type CabecalhoNotificacoesProps = {
  stockAlertCount: number | null;
  financeOverdueCount: number | null;
};

export function CabecalhoNotificacoes({ stockAlertCount, financeOverdueCount }: CabecalhoNotificacoesProps) {
  const { token } = theme.useToken();
  const { notification } = App.useApp();
  const { user } = useAutenticacao();
  const cap = user?.capacidades;
  const summaryEnabled = Boolean(cap?.painel);
  const { summary, loading: summaryLoading } = useResumoNotificacoes(summaryEnabled);
  const { items, unreadCount, loading, markRead, markAllRead } = useNotificacoes();
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
      const st = summary.estoque_abaixo_minimo;
      const ov = summary.financeiro.vencidos;
      const ds = summary.financeiro.a_vencer;
      return (
        <div style={{ marginBottom: 10 }}>
          <Typography.Text type="secondary" style={{ fontSize: 11, textTransform: "uppercase" }}>
            Alertas do sistema
          </Typography.Text>
          {cap?.estoque_leitura && st.quantidade > 0 ? (
            <div style={{ marginTop: 8 }}>
              <Link to="/app/estoque/alertas" style={{ fontWeight: 600, fontSize: 13 }}>
                Estoque abaixo do mínimo ({st.quantidade})
              </Link>
              {st.previa.length ? (
                <ul style={{ margin: "6px 0 0", paddingLeft: 18, fontSize: 12, color: token.colorTextSecondary }}>
                  {st.previa.slice(0, 5).map((p) => (
                    <li key={p.sku}>
                      <Typography.Text ellipsis style={{ maxWidth: 260, display: "inline-block", verticalAlign: "bottom" }}>
                        {p.nome} ({p.sku})
                      </Typography.Text>
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>
          ) : null}
          {cap?.financeiro && (ov.contagem_pagar > 0 || ov.contagem_receber > 0) ? (
            <div style={{ marginTop: 10 }}>
              <Link to="/app/financeiro/alertas" style={{ fontWeight: 600, fontSize: 13 }}>
                Títulos vencidos
              </Link>
              <Typography.Paragraph type="secondary" style={{ marginBottom: 0, marginTop: 4, fontSize: 12 }}>
                A pagar: {ov.contagem_pagar} ({formatMoneyBRL(ov.total_pagar)}) · A receber: {ov.contagem_receber} (
                {formatMoneyBRL(ov.total_receber)})
              </Typography.Paragraph>
            </div>
          ) : null}
          {cap?.financeiro && (ds.contagem_pagar > 0 || ds.contagem_receber > 0) ? (
            <div style={{ marginTop: 10 }}>
              <Link to="/app/financeiro/alertas" style={{ fontWeight: 600, fontSize: 13 }}>
                Vencendo em até {summary.financeiro.dias_a_frente} dias
              </Link>
              <Typography.Paragraph type="secondary" style={{ marginBottom: 0, marginTop: 4, fontSize: 12 }}>
                A pagar: {ds.contagem_pagar} · A receber: {ds.contagem_receber}
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
        {cap?.estoque_leitura && stockAlertCount != null && stockAlertCount > 0 ? (
          <div style={{ marginTop: 8 }}>
            <Link to="/app/estoque/alertas" style={{ fontWeight: 600, fontSize: 13 }}>
              Estoque abaixo do mínimo ({stockAlertCount})
            </Link>
          </div>
        ) : null}
        {cap?.financeiro && financeOverdueCount != null && financeOverdueCount > 0 ? (
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
              if (!n.lida_em) void markRead(n.id);
            }}
            style={{
              width: "100%",
              textAlign: "left",
              border: "none",
              background: n.lida_em ? "transparent" : token.colorFillAlter,
              borderRadius: token.borderRadius,
              padding: "8px 10px",
              marginBottom: 6,
              cursor: n.lida_em ? "default" : "pointer",
              display: "flex",
              gap: 10,
              alignItems: "flex-start",
              borderLeft: `3px solid ${
                n.nivel === "success"
                  ? token.colorSuccess
                  : n.nivel === "error"
                    ? token.colorError
                    : n.nivel === "warning"
                      ? token.colorWarning
                      : token.colorInfo
              }`,
            }}
          >
            <span style={{ marginTop: 2 }} aria-hidden>
              {levelIcon(n.nivel, token.colorSuccess, token.colorError, token.colorWarning)}
            </span>
            <span style={{ minWidth: 0, flex: 1 }}>
              <Typography.Text strong style={{ display: "block", fontSize: 13 }}>
                {n.titulo}
              </Typography.Text>
              {n.mensagem ? (
                <Typography.Paragraph
                  type="secondary"
                  ellipsis={{ rows: 2 }}
                  style={{ marginBottom: 4, fontSize: 12 }}
                >
                  {n.mensagem}
                </Typography.Paragraph>
              ) : null}
              <Typography.Text type="secondary" style={{ fontSize: 11 }}>
                {formatWhen(n.criado_em)}
                {n.lida_em ? " · Lida" : ""}
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
