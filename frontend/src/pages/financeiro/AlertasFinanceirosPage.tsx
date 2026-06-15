import { useCallback, useEffect, useState } from "react";
import {
  Alert,
  Button,
  Card,
  InputNumber,
  Space,
  Spin,
  Table,
  Typography,
} from "antd";
import { obterAlertasFinanceiros } from "../../api/financeiro";
import type { RespostaAlertasFinanceiros, AlertaContaPagar, AlertaContaReceber } from "../../types/financeiro";
import type { ColumnsType } from "antd/es/table";

const payableCols: ColumnsType<AlertaContaPagar> = [
  { title: "Vencimento", dataIndex: "vencimento", key: "vencimento" },
  { title: "Descrição", dataIndex: "descricao", key: "descricao" },
  { title: "Fornecedor", dataIndex: "nome_fornecedor", key: "nome_fornecedor", render: (v) => v ?? "—" },
  { title: "Valor", dataIndex: "valor", key: "valor" },
];

const receivableCols: ColumnsType<AlertaContaReceber> = [
  { title: "Vencimento", dataIndex: "vencimento", key: "vencimento" },
  { title: "Descrição", dataIndex: "descricao", key: "descricao" },
  { title: "Cliente", dataIndex: "nome_cliente", key: "nome_cliente", render: (v) => v ?? "—" },
  { title: "Valor", dataIndex: "valor", key: "valor" },
];

export function AlertasFinanceirosPage() {
  const [daysAhead, setDaysAhead] = useState(7);
  const [data, setData] = useState<RespostaAlertasFinanceiros | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const res = await obterAlertasFinanceiros(daysAhead);
      setData(res);
    } catch (e) {
      setData(null);
      setErr(e instanceof Error ? e.message : "Erro ao carregar alertas");
    } finally {
      setLoading(false);
    }
  }, [daysAhead]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Typography.Title level={3} style={{ margin: 0 }}>
        Alertas financeiros
      </Typography.Title>
      <Typography.Paragraph type="secondary">
        Títulos em aberto: vencidos e a vencer no período indicado (a partir de hoje).
      </Typography.Paragraph>

      <Card size="small" title="Parâmetros">
        <Space wrap align="center">
          <Typography.Text type="secondary">Dias à frente</Typography.Text>
          <InputNumber min={0} max={365} value={daysAhead} onChange={(v) => setDaysAhead(Number(v) || 0)} />
          <Button onClick={() => void load()} loading={loading}>
            Atualizar
          </Button>
        </Space>
      </Card>

      {err ? <Alert type="error" message={err} showIcon /> : null}

      <Spin spinning={loading}>
        {data ? (
          <>
            <Typography.Paragraph type="secondary">
              Referência: {data.today} · Janela até {data.until} ({data.days_ahead} dias)
            </Typography.Paragraph>

            <Typography.Title level={4}>Vencidos</Typography.Title>
            <Typography.Title level={5}>Contas a pagar</Typography.Title>
            <Table<AlertaContaPagar>
              rowKey="id"
              columns={payableCols}
              dataSource={data.overdue.payables}
              pagination={false}
              locale={{ emptyText: "Nenhum item." }}
            />
            <Typography.Title level={5} style={{ marginTop: 16 }}>
              Contas a receber
            </Typography.Title>
            <Table<AlertaContaReceber>
              rowKey="id"
              columns={receivableCols}
              dataSource={data.overdue.receivables}
              pagination={false}
              locale={{ emptyText: "Nenhum item." }}
            />

            <Typography.Title level={4} style={{ marginTop: 24 }}>
              A vencer
            </Typography.Title>
            <Typography.Title level={5}>Contas a pagar</Typography.Title>
            <Table<AlertaContaPagar>
              rowKey="id"
              columns={payableCols}
              dataSource={data.due_soon.payables}
              pagination={false}
              locale={{ emptyText: "Nenhum item." }}
            />
            <Typography.Title level={5} style={{ marginTop: 16 }}>
              Contas a receber
            </Typography.Title>
            <Table<AlertaContaReceber>
              rowKey="id"
              columns={receivableCols}
              dataSource={data.due_soon.receivables}
              pagination={false}
              locale={{ emptyText: "Nenhum item." }}
            />
          </>
        ) : null}
      </Spin>
    </Space>
  );
}
