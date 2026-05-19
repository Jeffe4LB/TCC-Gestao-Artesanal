import { useCallback, useEffect, useMemo, useState } from "react";
import { Alert, Button, Card, Input, Select, Space, Spin, Table, Typography } from "antd";
import { fetchAllCategories } from "../../api/catalog";
import {
  downloadStockPositionCsv,
  fetchStockPositionReport,
} from "../../api/reports";
import type { Category } from "../../types/catalog";
import type { StockPositionReport, StockPositionRow } from "../../types/reports";
import type { ColumnsType } from "antd/es/table";
import { formatQuantityDisplay } from "../../utils/quantityDisplay";

export function ReportStockPositionPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [category, setCategory] = useState("");
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [data, setData] = useState<StockPositionReport | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    void fetchAllCategories().then(setCategories).catch(() => {});
  }, []);

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const res = await fetchStockPositionReport({
        category: category || undefined,
        search: search || undefined,
      });
      setData(res);
    } catch (e) {
      setData(null);
      setErr(e instanceof Error ? e.message : "Erro ao gerar");
    } finally {
      setLoading(false);
    }
  }, [category, search]);

  useEffect(() => {
    void load();
  }, [load]);

  const exportCsv = async () => {
    setExporting(true);
    setErr(null);
    try {
      await downloadStockPositionCsv({
        category: category || undefined,
        search: search || undefined,
      });
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao exportar");
    } finally {
      setExporting(false);
    }
  };

  const columns: ColumnsType<StockPositionRow> = useMemo(
    () => [
      { title: "SKU", dataIndex: "sku", key: "sku" },
      { title: "Nome", dataIndex: "name", key: "name" },
      { title: "Categoria", dataIndex: "category", key: "category", render: (v) => v || "—" },
      {
        title: "Saldo",
        dataIndex: "quantity",
        key: "quantity",
        render: (v: string) => formatQuantityDisplay(v),
      },
      {
        title: "Mín.",
        dataIndex: "min_stock",
        key: "min_stock",
        render: (v: string) => formatQuantityDisplay(v),
      },
      {
        title: "Abaixo?",
        dataIndex: "below_minimum",
        key: "below_minimum",
        render: (v: boolean) => (v ? "Sim" : "Não"),
      },
    ],
    [],
  );

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Typography.Title level={3} style={{ margin: 0 }}>
        Posição de estoque
      </Typography.Title>

      <Card size="small" title="Filtros">
        <Space wrap>
          <Select
            placeholder="Categoria"
            value={category || undefined}
            onChange={(v) => setCategory(v ?? "")}
            allowClear
            style={{ width: 220 }}
            options={categories.map((c) => ({ value: String(c.id), label: c.name }))}
          />
          <Input
            placeholder="Buscar SKU ou nome"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onPressEnter={() => setSearch(searchInput.trim())}
            style={{ width: 220 }}
            allowClear
          />
          <Button type="primary" onClick={() => setSearch(searchInput.trim())}>
            Filtrar
          </Button>
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
        <Typography.Text type="secondary">{data.count} registro(s)</Typography.Text>
      ) : null}

      <Spin spinning={loading && !data}>
        {data ? (
          <Table<StockPositionRow>
            rowKey="sku"
            columns={columns}
            dataSource={data.results}
            pagination={false}
          />
        ) : null}
      </Spin>
    </Space>
  );
}
