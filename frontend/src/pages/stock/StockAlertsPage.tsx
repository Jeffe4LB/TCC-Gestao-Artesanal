import { useCallback, useEffect, useMemo, useState } from "react";
import { Alert, Button, Card, Input, Space, Spin, Table, Typography } from "antd";
import { PaginationBar } from "../../components/PaginationBar";
import { listStockAlerts } from "../../api/stock";
import type { StockAlertRow } from "../../types/stock";
import type { ColumnsType } from "antd/es/table";
import { formatQuantityDisplay } from "../../utils/quantityDisplay";

const PAGE_SIZE = 20;

export function StockAlertsPage() {
  const [list, setList] = useState<StockAlertRow[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const data = await listStockAlerts({
        page,
        search: search || undefined,
      });
      setList(data.results);
      setCount(data.count);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao listar");
    } finally {
      setLoading(false);
    }
  }, [page, search]);

  useEffect(() => {
    void load();
  }, [load]);

  const columns: ColumnsType<StockAlertRow> = useMemo(
    () => [
      { title: "SKU", dataIndex: "sku", key: "sku" },
      { title: "Produto", dataIndex: "name", key: "name" },
      {
        title: "Mínimo",
        dataIndex: "min_stock",
        key: "min_stock",
        render: (v: string) => formatQuantityDisplay(v),
      },
      {
        title: "Atual",
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
        Alertas de estoque
      </Typography.Title>
      <Typography.Paragraph type="secondary">
        Produtos com saldo atual menor ou igual ao estoque mínimo (exclui mínimo zero).
      </Typography.Paragraph>

      <Card size="small" title="Buscar">
        <Space wrap>
          <Input
            placeholder="Buscar SKU ou nome"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onPressEnter={() => {
              setPage(1);
              setSearch(searchInput.trim());
            }}
            style={{ width: 220 }}
            allowClear
          />
          <Button
            type="primary"
            onClick={() => {
              setPage(1);
              setSearch(searchInput.trim());
            }}
          >
            Buscar
          </Button>
        </Space>
      </Card>

      {err ? <Alert type="error" message={err} showIcon /> : null}

      <Spin spinning={loading}>
        <Table<StockAlertRow>
          rowKey="product_id"
          columns={columns}
          dataSource={list}
          pagination={false}
        />
        <PaginationBar page={page} totalCount={count} pageSize={PAGE_SIZE} onPageChange={setPage} />
      </Spin>
    </Space>
  );
}
