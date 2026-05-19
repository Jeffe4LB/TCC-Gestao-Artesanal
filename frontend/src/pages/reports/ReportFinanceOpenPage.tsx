import { useCallback, useEffect, useMemo, useState } from "react";
import { Alert, Button, Card, Space, Spin, Table, Typography } from "antd";
import { downloadFinanceOpenCsv, fetchFinanceOpenReport } from "../../api/reports";
import type {
  FinanceOpenPayableRow,
  FinanceOpenReceivableRow,
  FinanceOpenReport,
} from "../../types/reports";
import type { ColumnsType } from "antd/es/table";

export function ReportFinanceOpenPage() {
  const [data, setData] = useState<FinanceOpenReport | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const res = await fetchFinanceOpenReport();
      setData(res);
    } catch (e) {
      setData(null);
      setErr(e instanceof Error ? e.message : "Erro ao gerar");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const exportCsv = async () => {
    setExporting(true);
    setErr(null);
    try {
      await downloadFinanceOpenCsv();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao exportar");
    } finally {
      setExporting(false);
    }
  };

  const payableCols: ColumnsType<FinanceOpenPayableRow> = useMemo(
    () => [
      { title: "ID", dataIndex: "id", key: "id", width: 72 },
      { title: "Descrição", dataIndex: "description", key: "description" },
      { title: "Valor", dataIndex: "amount", key: "amount" },
      { title: "Vencimento", dataIndex: "due_date", key: "due_date" },
      { title: "Fornecedor", dataIndex: "supplier", key: "supplier", render: (v) => v ?? "—" },
    ],
    [],
  );

  const receivableCols: ColumnsType<FinanceOpenReceivableRow> = useMemo(
    () => [
      { title: "ID", dataIndex: "id", key: "id", width: 72 },
      { title: "Descrição", dataIndex: "description", key: "description" },
      { title: "Valor", dataIndex: "amount", key: "amount" },
      { title: "Vencimento", dataIndex: "due_date", key: "due_date" },
      { title: "Cliente", dataIndex: "customer", key: "customer", render: (v) => v ?? "—" },
    ],
    [],
  );

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Typography.Title level={3} style={{ margin: 0 }}>
        Contas em aberto
      </Typography.Title>
      <Typography.Paragraph type="secondary">
        Títulos com status em aberto, ordenados por vencimento.
      </Typography.Paragraph>

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
            <Card size="small" title="Resumo">
              <Typography.Paragraph>
                A pagar: <strong>{data.summary.payables_count}</strong> (R$ {data.summary.payables_total})
                {" · "}
                A receber: <strong>{data.summary.receivables_count}</strong> (R${" "}
                {data.summary.receivables_total})
              </Typography.Paragraph>
              <Typography.Paragraph style={{ marginBottom: 0 }}>
                Saldo em aberto (receber − pagar): <strong>R$ {data.summary.net_open}</strong>
              </Typography.Paragraph>
            </Card>

            <Typography.Title level={4}>Contas a pagar</Typography.Title>
            <Table<FinanceOpenPayableRow>
              rowKey="id"
              columns={payableCols}
              dataSource={data.payables}
              pagination={false}
              scroll={{ x: true }}
            />

            <Typography.Title level={4} style={{ marginTop: 24 }}>
              Contas a receber
            </Typography.Title>
            <Table<FinanceOpenReceivableRow>
              rowKey="id"
              columns={receivableCols}
              dataSource={data.receivables}
              pagination={false}
              scroll={{ x: true }}
            />
          </>
        ) : null}
      </Spin>
    </Space>
  );
}
