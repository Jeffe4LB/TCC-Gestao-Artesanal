import { useCallback, useEffect, useState } from "react";
import { Alert, Button, Card, Col, DatePicker, Form, Row, Space, Spin, Statistic, Typography } from "antd";
import dayjs from "dayjs";
import { getCashFlow } from "../../api/finance";
import type { CashFlowResponse } from "../../types/finance";

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

export function CashFlowPage() {
  const [from, setFrom] = useState(firstDayOfMonthLocal);
  const [to, setTo] = useState(todayLocal);
  const [data, setData] = useState<CashFlowResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const res = await getCashFlow(from, to);
      setData(res);
    } catch (e) {
      setData(null);
      setErr(e instanceof Error ? e.message : "Erro ao carregar fluxo");
    } finally {
      setLoading(false);
    }
  }, [from, to]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Typography.Title level={3} style={{ margin: 0 }}>
        Fluxo de caixa
      </Typography.Title>
      <Typography.Paragraph type="secondary">
        Entradas e saídas pela data efetiva (recebido em / pago em), apenas lançamentos com status
        recebido ou pago.
      </Typography.Paragraph>

      <Card size="small" title="Período">
        <Form layout="inline" onFinish={() => void load()}>
          <Form.Item label="De">
            <DatePicker
              format="YYYY-MM-DD"
              value={dayjs(from)}
              onChange={(_, s) => setFrom(typeof s === "string" ? s : firstDayOfMonthLocal())}
            />
          </Form.Item>
          <Form.Item label="Até">
            <DatePicker
              format="YYYY-MM-DD"
              value={dayjs(to)}
              onChange={(_, s) => setTo(typeof s === "string" ? s : todayLocal())}
            />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              Atualizar
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {err ? <Alert type="error" message={err} showIcon /> : null}

      <Spin spinning={loading}>
        {data ? (
          <>
            <Row gutter={[16, 16]}>
              <Col xs={24} md={8}>
                <Card>
                  <Statistic title="Entradas" value={data.inflows} prefix="R$ " />
                </Card>
              </Col>
              <Col xs={24} md={8}>
                <Card>
                  <Statistic title="Saídas" value={data.outflows} prefix="R$ " />
                </Card>
              </Col>
              <Col xs={24} md={8}>
                <Card>
                  <Statistic title="Saldo (líquido)" value={data.net} prefix="R$ " />
                </Card>
              </Col>
            </Row>
            <Typography.Text type="secondary">
              Período: {data.from} a {data.to}
            </Typography.Text>
          </>
        ) : null}
      </Spin>
    </Space>
  );
}
