import { useCallback, useEffect, useState } from "react";
import {
  Alert,
  Button,
  Card,
  Col,
  InputNumber,
  Row,
  Space,
  Spin,
  Statistic,
  Typography,
} from "antd";
import { Link } from "react-router-dom";
import { ReloadOutlined } from "@ant-design/icons";
import { getCashFlow } from "../api/finance";
import { fetchNotificationSummary } from "../api/notifications";
import { useToast } from "../hooks/useToast";
import type { CashFlowResponse } from "../types/finance";
import type { NotificationSummary } from "../types/notifications";
import { StatCard } from "../components/StatCard";
import { DatePicker } from "antd";

const colors = {
  success: "#52c41a",
  warning: "#faad14",
  error: "#ff4d4f",
  info: "#1677ff",
};

function firstDayOfMonthLocal(): string {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  return `${y}-${m}-01`;
}

function todayLocal(): string {
  const d = new Date();
  const y = d.getFullYear();
  const mo = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${mo}-${day}`;
}

export function DashboardPage() {
  const { showToast } = useToast();

  const [daysAhead, setDaysAhead] = useState(7);
  const [summary, setSummary] = useState<NotificationSummary | null>(null);
  const [cashFlow, setCashFlow] = useState<CashFlowResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [dateRange, setDateRange] = useState<[string, string] | null>(null);

  const loadAll = useCallback(
    async (opts?: { silent?: boolean }) => {
      setLoading(true);
      setErr(null);

      //const from = firstDayOfMonthLocal();
      //const to = todayLocal();

      const from = dateRange ? dateRange[0] : firstDayOfMonthLocal();
      const to = dateRange ? dateRange[1] : todayLocal(); 

      try {
        //const sum = await fetchNotificationSummary(daysAhead, 10);
        const sum = await fetchNotificationSummary(daysAhead, 10, from, to);
        setSummary(sum);

        try {
          const cf = await getCashFlow(from, to);
          setCashFlow(cf);
        } catch {
          setCashFlow(null);
        }

        if (!opts?.silent) {
          showToast("Dashboard atualizado", "success");
        }
      } catch (e) {
        const msg =
          e instanceof Error ? e.message : "Erro ao carregar dashboard";
        setErr(msg);
        showToast(msg, "error");
      } finally {
        setLoading(false);
      }
    },
    [daysAhead, showToast, dateRange]
  );

  useEffect(() => {
    void loadAll({ silent: true });
  }, [loadAll]);

  const financeOverdueTotal = summary
    ? summary.finance.overdue.payables_count +
      summary.finance.overdue.receivables_count
    : 0;

  return (
    <Space
      direction="vertical"
      size="large"
      style={{ width: "100%", padding: 24 }}
    >
      {/* HEADER */}
      <Row justify="space-between" align="middle" gutter={[16, 16]}>
        <Col flex="1">
          <Typography.Title level={3} style={{ marginBottom: 0 }}>
            Dashboard
          </Typography.Title>

          <Typography.Text type="secondary">
            Resumo
          </Typography.Text>

          {summary && (
            <Typography.Text
              type="secondary"
              style={{ fontSize: 12, display: "block" }}
            >
              Última atualização:{" "}
              {new Date(summary.generated_at).toLocaleString("pt-BR")}
            </Typography.Text>
          )}
        </Col>

        <Col>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => void loadAll({ silent: false })}
            loading={loading}
          >
            Atualizar dados
          </Button>
        </Col>
      </Row>

      {/* PARÂMETROS */}
      <Card size="small" title="Parâmetros">
        <Space wrap align="center">
          <Typography.Text type="secondary">
            Dias à frente (financeiro)
          </Typography.Text>
          <InputNumber
            min={0}
            max={365}
            value={daysAhead}
            onChange={(v) => setDaysAhead(Number(v) || 0)}
          />

          <Typography.Text type="secondary">
            Período
          </Typography.Text>

          <DatePicker.RangePicker
            format="DD/MM/YYYY"
            onChange={(dates) => {
              const [start, end] = dates ?? [];
              if (start && end) {
                setDateRange([
                  start.format("YYYY-MM-DD"),
                  end.format("YYYY-MM-DD"),
                ]);
              } else {
                setDateRange(null);
              }
            }}
          />


        </Space>
      </Card>

      {/* ERRO */}
      {err && <Alert type="error" message={err} showIcon />}

      {/* KPI CARDS */}
      <Spin spinning={loading}>
        {summary && (
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} lg={6}>
              <StatCard
                title="Estoque crítico"
                value={summary.stock_below_minimum.count}
                color={colors.warning}
                subtitle="abaixo do mínimo"
              />
            </Col>

            <Col xs={24} sm={12} lg={6}>
              <StatCard
                title="Títulos vencidos"
                value={financeOverdueTotal}
                color={
                  financeOverdueTotal > 0
                    ? colors.error
                    : colors.success
                }
                subtitle="pagar + receber"
              />
            </Col>

            <Col xs={24} sm={12} lg={6}>
              <StatCard
                title="Contas a pagar"
                value={summary.finance.overdue.payables_count}
                color={colors.error}
                subtitle="em aberto"
              />
            </Col>

            <Col xs={24} sm={12} lg={6}>
              <StatCard
                title="Contas a receber"
                value={summary.finance.overdue.receivables_count}
                color={colors.info}
                subtitle="em aberto"
              />
            </Col>
          </Row>
        )}
      </Spin>

      {/* FLUXO DE CAIXA */}
      {cashFlow && (
        <Card
          style={{ marginTop: 0 }}
          title="Fluxo de caixa"
          extra={
            <Typography.Text type="secondary">
              {cashFlow.from} → {cashFlow.to}
            </Typography.Text>
          }
        >
          <Row gutter={[16, 16]}>
            <Col xs={24} md={8}>
              <Statistic
                title="Entradas"
                value={cashFlow.inflows}
                precision={2}
                prefix="R$"
                valueStyle={{ color: colors.success }}
              />
            </Col>

            <Col xs={24} md={8}>
              <Statistic
                title="Saídas"
                value={cashFlow.outflows}
                precision={2}
                prefix="R$"
                valueStyle={{ color: colors.error }}
              />
            </Col>

            <Col xs={24} md={8}>
              <Statistic
                title="Líquido"
                value={cashFlow.net}
                precision={2}
                prefix="R$"
                valueStyle={{
                  color:
                    Number(cashFlow.net) >= 0
                      ? colors.success
                      : colors.error,
                }}
              />
            </Col>
          </Row>

          <Link to="/app/financeiro/fluxo-caixa">
            <Typography.Link>
              Ver fluxo com período customizado →
            </Typography.Link>
          </Link>
        </Card>
      )}

      {/* OUTROS CARDS */}
      {summary && (
        <Row gutter={[16, 16]}>
          <Col xs={24} md={12}>
            <Card title="Estoque">
              <Typography.Paragraph type="secondary">
                {summary.stock_below_minimum.count} produto(s) com saldo
                igual ou inferior ao mínimo configurado.
              </Typography.Paragraph>

              <Link to="/app/estoque/alertas">
                <Button type="primary">
                  Abrir alertas de estoque
                </Button>
              </Link>
            </Card>
          </Col>

          <Col xs={24} md={12}>
            <Card title="Financeiro">
              <Typography.Paragraph>
                <Typography.Text type="secondary">
                  A vencer até {summary.finance.until}
                </Typography.Text>
                <br />

                <strong>
                  {summary.finance.due_soon.payables_count} pagar ·{" "}
                  {summary.finance.due_soon.receivables_count} receber
                </strong>
              </Typography.Paragraph>

              <Space wrap>
                <Link to="/app/financeiro/alertas">
                  <Button>Alertas</Button>
                </Link>

                <Link to="/app/financeiro/pagar">
                  <Button>A pagar</Button>
                </Link>

                <Link to="/app/financeiro/receber">
                  <Button>A receber</Button>
                </Link>
              </Space>
            </Card>
          </Col>
        </Row>
      )}
    </Space>
  );
}