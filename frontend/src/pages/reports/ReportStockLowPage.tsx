import { useCallback, useEffect, useMemo, useState } from "react";
import { Alert, Button, Card, Form, Input, Space, Spin, Table, Typography } from "antd";
import { downloadStockLowCsv, fetchStockLowReport } from "../../api/reports";
import type { StockLowReport, StockLowRow } from "../../types/reports";
import type { ColumnsType } from "antd/es/table";
import { formatQuantityDisplay } from "../../utils/quantityDisplay";

export function ReportStockLowPage() {
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [data, setData] = useState<StockLowReport | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const res = await fetchStockLowReport({
        search: search || undefined,
      });
      setData(res);
    } catch (e) {
      setData(null);
      setErr(e instanceof Error ? e.message : "Erro ao gerar");
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => {
    void load();
  }, [load]);

  const exportCsv = async () => {
    setExporting(true);
    setErr(null);
    try {
      await downloadStockLowCsv({ search: search || undefined });
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao exportar");
    } finally {
      setExporting(false);
    }
  };

  const columns: ColumnsType<StockLowRow> = useMemo(
    () => [
      { title: "SKU", dataIndex: "sku", key: "sku" },
      { title: "Nome", dataIndex: "name", key: "name" },
      {
        title: "Mínimo",
        dataIndex: "min_stock",
        key: "min_stock",
        render: (v: string) => formatQuantityDisplay(v),
      },
      {
        title: "Saldo",
        dataIndex: "current_quantity",
        key: "current_quantity",
        render: (v: string) => formatQuantityDisplay(v),
      },
      {
        title: "Falta",
        dataIndex: "gap",
        key: "gap",
        render: (v: string) => formatQuantityDisplay(v),
      },
    ],
    [],
  );

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Typography.Title level={3} style={{ margin: 0 }}>
        Estoque abaixo do mínimo
      </Typography.Title>

      <Card size="small" title="Filtros">
        <Form layout="inline" onFinish={() => setSearch(searchInput.trim())}>
          <Form.Item>
            <Input
              placeholder="Buscar SKU ou nome"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              allowClear
            />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit">
              Filtrar
            </Button>
          </Form.Item>
        </Form>
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

      {data ? <Typography.Text type="secondary">{data.count} registro(s)</Typography.Text> : null}

      <Spin spinning={loading && !data}>
        {data ? (
          <Table<StockLowRow> rowKey="sku" columns={columns} dataSource={data.results} pagination={false} />
        ) : null}
      </Spin>
    </Space>
  );
}
