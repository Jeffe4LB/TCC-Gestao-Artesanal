import { useCallback, useEffect, useMemo, useState } from "react";
import { Alert, Button, Card, DatePicker, Select, Space, Spin, Table, Typography } from "antd";
import dayjs from "dayjs";
import { fetchAllProducts } from "../../api/catalog";
import {
  downloadStockMovementsCsv,
  fetchStockMovementsReport,
} from "../../api/reports";
import type { Product } from "../../types/catalog";
import type { StockMovementReportRow, StockMovementsReport } from "../../types/reports";
import { firstDayOfMonthLocal, todayLocal } from "./dateRange";
import type { ColumnsType } from "antd/es/table";
import { formatQuantityDisplay } from "../../utils/quantityDisplay";

const MOV_LABEL: Record<string, string> = {
  purchase_in: "Compra",
  adjustment: "Ajuste",
  production_consumption: "Consumo (produção)",
  production_output: "Saída produto acabado",
  receivable_sale: "Venda (conta a receber)",
  receivable_sale_reversal: "Estorno venda (conta a receber)",
};

export function ReportStockMovementsPage() {
  const [from, setFrom] = useState(firstDayOfMonthLocal);
  const [to, setTo] = useState(todayLocal);
  const [product, setProduct] = useState("");
  const [movementType, setMovementType] = useState("");
  const [products, setProducts] = useState<Product[]>([]);
  const [data, setData] = useState<StockMovementsReport | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    void fetchAllProducts({ is_active: true }).then(setProducts).catch(() => {});
  }, []);

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const res = await fetchStockMovementsReport({
        from,
        to,
        product: product ? Number(product) : undefined,
        movement_type: movementType || undefined,
        limit: 500,
      });
      setData(res);
    } catch (e) {
      setData(null);
      setErr(e instanceof Error ? e.message : "Erro ao gerar");
    } finally {
      setLoading(false);
    }
  }, [from, to, product, movementType]);

  useEffect(() => {
    void load();
  }, [load]);

  const exportCsv = async () => {
    setExporting(true);
    setErr(null);
    try {
      await downloadStockMovementsCsv({
        from,
        to,
        product: product ? Number(product) : undefined,
        movement_type: movementType || undefined,
        limit: 10000,
      });
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao exportar");
    } finally {
      setExporting(false);
    }
  };

  const columns: ColumnsType<StockMovementReportRow> = useMemo(
    () => [
      {
        title: "Data",
        dataIndex: "created_at",
        key: "created_at",
        render: (v: string) => new Date(v).toLocaleString(),
      },
      { title: "SKU", dataIndex: "sku", key: "sku" },
      { title: "Produto", dataIndex: "product_name", key: "product_name" },
      {
        title: "Δ",
        dataIndex: "quantity_delta",
        key: "quantity_delta",
        render: (v: string) => formatQuantityDisplay(v),
      },
      {
        title: "Tipo",
        dataIndex: "movement_type",
        key: "movement_type",
        render: (c: string) => MOV_LABEL[c] ?? c,
      },
      { title: "Obs.", dataIndex: "notes", key: "notes", render: (v) => v || "—" },
    ],
    [],
  );

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Typography.Title level={3} style={{ margin: 0 }}>
        Movimentações de estoque
      </Typography.Title>
      <Typography.Paragraph type="secondary">
        Período pela <strong>data do lançamento</strong> (campo criado em). Prévia limitada a 500 linhas;
        CSV até 10 mil.
      </Typography.Paragraph>

      <Card size="small" title="Filtros">
        <Space wrap>
          <DatePicker
            placeholder="De"
            format="YYYY-MM-DD"
            value={dayjs(from)}
            onChange={(_, s) => setFrom(typeof s === "string" && s ? s : firstDayOfMonthLocal())}
          />
          <DatePicker
            placeholder="Até"
            format="YYYY-MM-DD"
            value={dayjs(to)}
            onChange={(_, s) => setTo(typeof s === "string" && s ? s : todayLocal())}
          />
          <Select
            placeholder="Produto"
            value={product || undefined}
            onChange={(v) => setProduct(v ?? "")}
            allowClear
            showSearch
            optionFilterProp="label"
            style={{ width: 280 }}
            options={products.map((p) => ({
              value: String(p.id),
              label: `${p.sku} — ${p.name}`,
            }))}
          />
          <Select
            placeholder="Tipo"
            value={movementType || undefined}
            onChange={(v) => setMovementType(v ?? "")}
            allowClear
            style={{ width: 240 }}
            options={[
              { value: "purchase_in", label: "Compra" },
              { value: "adjustment", label: "Ajuste" },
              { value: "production_consumption", label: "Consumo (produção)" },
              { value: "production_output", label: "Saída produto acabado" },
              { value: "receivable_sale", label: "Venda (conta a receber)" },
              { value: "receivable_sale_reversal", label: "Estorno venda (conta a receber)" },
            ]}
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

      {data ? (
        <Typography.Text type="secondary">
          {data.from} a {data.to} · {data.count} linha(s) na prévia
        </Typography.Text>
      ) : null}

      <Spin spinning={loading && !data}>
        {data ? (
          <Table<StockMovementReportRow>
            rowKey="id"
            columns={columns}
            dataSource={data.results}
            pagination={false}
            scroll={{ x: true }}
          />
        ) : null}
      </Spin>
    </Space>
  );
}
