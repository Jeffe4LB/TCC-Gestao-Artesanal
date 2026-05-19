import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Alert, Button, Descriptions, Spin, Table, Typography } from "antd";
import { ArrowLeftOutlined } from "@ant-design/icons";
import { getProductionRun } from "../../api/stock";
import type { ProductionRun } from "../../types/stock";
import type { ColumnsType } from "antd/es/table";
import { formatQuantityDisplay } from "../../utils/quantityDisplay";

export function ProductionRunDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [run, setRun] = useState<ProductionRun | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) {
      setErr("ID inválido");
      setLoading(false);
      return;
    }
    let cancelled = false;
    void (async () => {
      setErr(null);
      setLoading(true);
      try {
        const data = await getProductionRun(Number(id));
        if (!cancelled) setRun(data);
      } catch (e) {
        if (!cancelled) setErr(e instanceof Error ? e.message : "Erro ao carregar");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id]);

  const lineColumns: ColumnsType<ProductionRun["lines"][number]> = [
    { title: "SKU", dataIndex: "component_sku", key: "component_sku" },
    { title: "Insumo", dataIndex: "component_name", key: "component_name" },
    {
      title: "Qtd consumida",
      dataIndex: "quantity_consumed",
      key: "quantity_consumed",
      render: (v: string) => formatQuantityDisplay(v),
    },
  ];

  if (loading) {
    return (
      <div style={{ padding: 48, textAlign: "center" }}>
        <Spin />
      </div>
    );
  }
  if (err || !run) {
    return <Alert type="error" message={err ?? "Não encontrado"} showIcon />;
  }

  return (
    <div>
      <Link to="/app/estoque/producao">
        <Button type="link" icon={<ArrowLeftOutlined />} style={{ paddingLeft: 0, marginBottom: 16 }}>
          Voltar à lista
        </Button>
      </Link>
      <Typography.Title level={3}>Produção #{run.id}</Typography.Title>
      <Descriptions bordered column={1} size="small" style={{ marginBottom: 24, maxWidth: 560 }}>
        <Descriptions.Item label="Produto">
          {run.product_sku} — {run.product_name}
        </Descriptions.Item>
        <Descriptions.Item label="Quantidade produzida">
          {formatQuantityDisplay(run.quantity_produced)}
        </Descriptions.Item>
        <Descriptions.Item label="Data">{new Date(run.created_at).toLocaleString()}</Descriptions.Item>
        {run.notes ? <Descriptions.Item label="Obs.">{run.notes}</Descriptions.Item> : null}
      </Descriptions>

      <Typography.Title level={4}>Consumo de insumos</Typography.Title>
      <Table
        rowKey="id"
        columns={lineColumns}
        dataSource={run.lines}
        pagination={false}
        size="small"
      />
    </div>
  );
}
