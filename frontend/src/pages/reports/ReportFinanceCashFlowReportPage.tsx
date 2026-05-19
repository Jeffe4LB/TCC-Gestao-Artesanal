import { useCallback, useEffect, useState } from "react";
import {
  Alert,
  Button,
  Card,
  Col,
  DatePicker,
  Row,
  Space,
  Spin,
  Statistic,
  Typography,
} from "antd";
import dayjs from "dayjs";
import {
  downloadFinanceCashFlowCsv,
  fetchFinanceCashFlowReport,
} from "../../api/reports";
import type { FinanceCashFlowReport } from "../../types/reports";
import { firstDayOfMonthLocal, todayLocal } from "./dateRange";

export function ReportFinanceCashFlowReportPage() {
  const [from, setFrom] = useState(firstDayOfMonthLocal);
  const [to, setTo] = useState(todayLocal);
  const [data, setData] = useState<FinanceCashFlowReport | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const res = await fetchFinanceCashFlowReport(from, to);
      setData(res);
    } catch (e) {
      setData(null);
      setErr(e instanceof Error ? e.message : "Erro ao gerar");
    } finally {
      setLoading(false);
    }
  }, [from, to]);

  useEffect(() => {
    void load();
  }, [load]);

  const exportCsv = async () => {
    setExporting(true);
    setErr(null);
    try {
      await downloadFinanceCashFlowCsv(from, to);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao exportar");
    } finally {
      setExporting(false);
    }
  };

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Typography.Title level={3} style={{ margin: 0 }}>
        Fluxo de caixa (relatório)
      </Typography.Title>
      <Typography.Paragraph type="secondary">
        Mesma regra do módulo financeiro: entradas e saídas pela data efetiva (recebido/pago).
      </Typography.Paragraph>

      <Card size="small" title="Período">
        <Space wrap>
          <DatePicker
            format="YYYY-MM-DD"
            value={dayjs(from)}
            onChange={(_, s) => setFrom(typeof s === "string" && s ? s : firstDayOfMonthLocal())}
          />
          <DatePicker
            format="YYYY-MM-DD"
            value={dayjs(to)}
            onChange={(_, s) => setTo(typeof s === "string" && s ? s : todayLocal())}
          />
        </Space>
      </Card>

      <Space wrap>
        <Button onClick={() => void load()} loading={loading}>
          Atualizar prévia
        </Button>
        <Button type="primary" onClick={() => void exportCsv()} loading={exporting}>
          Exportar CSV
        </Button>
      </Space>

      {err ? <Alert type="error" message={err} showIcon /> : null}

      <Spin spinning={loading && !data}>
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
                  <Statistic title="Líquido" value={data.net} prefix="R$ " />
                </Card>
              </Col>
            </Row>
            <Typography.Text type="secondary">
              {data.from} a {data.to}
            </Typography.Text>
          </>
        ) : null}
      </Spin>
    </Space>
  );
}
