import { useCallback, useEffect, useMemo, useState } from "react";
import { Alert, Button, Space, Spin, Table, Typography } from "antd";
import { downloadFinanceAgingCsv, fetchFinanceAgingReport } from "../../api/reports";
import type { FinanceAgingReport } from "../../types/reports";
import type { ColumnsType } from "antd/es/table";

const BUCKET_ORDER = [
  "overdue",
  "due_next_7_days",
  "due_8_to_30_days",
  "due_after_30_days",
] as const;

const BUCKET_LABEL: Record<(typeof BUCKET_ORDER)[number], string> = {
  overdue: "Vencidas",
  due_next_7_days: "Vence em até 7 dias",
  due_8_to_30_days: "Vence em 8 a 30 dias",
  due_after_30_days: "Vence após 30 dias",
};

type BucketRow = {
  key: string;
  faixa: string;
  qtd: number;
  total: string;
};

function useBucketColumns(): ColumnsType<BucketRow> {
  return useMemo(
    () => [
      { title: "Faixa", dataIndex: "faixa", key: "faixa" },
      { title: "Qtd", dataIndex: "qtd", key: "qtd" },
      { title: "Total (R$)", dataIndex: "total", key: "total" },
    ],
    [],
  );
}

function bucketRows(buckets: FinanceAgingReport["payables"]): BucketRow[] {
  return BUCKET_ORDER.map((key) => ({
    key,
    faixa: BUCKET_LABEL[key],
    qtd: buckets[key]?.count ?? 0,
    total: buckets[key]?.total ?? "0",
  }));
}

function BucketTable({
  title,
  buckets,
  columns,
}: {
  title: string;
  buckets: FinanceAgingReport["payables"];
  columns: ColumnsType<BucketRow>;
}) {
  return (
    <>
      <Typography.Title level={4}>{title}</Typography.Title>
      <Table<BucketRow>
        rowKey="key"
        columns={columns}
        dataSource={bucketRows(buckets)}
        pagination={false}
        size="small"
      />
    </>
  );
}

export function ReportFinanceAgingPage() {
  const [data, setData] = useState<FinanceAgingReport | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const columns = useBucketColumns();

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const res = await fetchFinanceAgingReport();
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
      await downloadFinanceAgingCsv();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao exportar");
    } finally {
      setExporting(false);
    }
  };

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Typography.Title level={3} style={{ margin: 0 }}>
        Envelhecimento de títulos
      </Typography.Title>
      <Typography.Paragraph type="secondary">
        Contas a pagar e a receber em aberto, agrupadas por faixa em relação à data base.
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
            <Typography.Text type="secondary">Data base: {data.today}</Typography.Text>
            <BucketTable title="Contas a pagar (em aberto)" buckets={data.payables} columns={columns} />
            <div style={{ marginTop: 16 }}>
              <BucketTable
                title="Contas a receber (em aberto)"
                buckets={data.receivables}
                columns={columns}
              />
            </div>
          </>
        ) : null}
      </Spin>
    </Space>
  );
}
