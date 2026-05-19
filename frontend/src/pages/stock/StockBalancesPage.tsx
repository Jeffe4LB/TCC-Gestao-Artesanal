import { useCallback, useEffect, useMemo, useState } from "react";
import { Alert, Button, Card, Input, Select, Space, Spin, Table, Typography } from "antd";
import { PaginationBar } from "../../components/PaginationBar";
import { fetchAllProducts } from "../../api/catalog";
import { listStockBalances } from "../../api/stock";
import type { Product } from "../../types/catalog";
import type { StockBalanceRow } from "../../types/stock";
import type { ColumnsType } from "antd/es/table";
import { formatQuantityWithUnit } from "../../utils/quantityDisplay";

const PAGE_SIZE = 20;

export function StockBalancesPage() {
  const [list, setList] = useState<StockBalanceRow[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [productId, setProductId] = useState<string>("");
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    void fetchAllProducts({ is_active: true }).then(setProducts).catch(() => {});
  }, []);

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const data = await listStockBalances({
        page,
        search: search || undefined,
        product: productId || undefined,
        ordering: "product__name",
      });
      setList(data.results);
      setCount(data.count);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao listar");
    } finally {
      setLoading(false);
    }
  }, [page, search, productId]);

  useEffect(() => {
    void load();
  }, [load]);

  const columns: ColumnsType<StockBalanceRow> = useMemo(
    () => [
      { title: "SKU", dataIndex: "product_sku", key: "product_sku" },
      { title: "Produto", dataIndex: "product_name", key: "product_name" },
      {
        title: "Saldo (base)",
        key: "qty_base",
        render: (_: unknown, r: StockBalanceRow) => formatQuantityWithUnit(r.quantity, r.base_unit),
      },
    ],
    [],
  );

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Typography.Title level={3} style={{ margin: 0 }}>
        Saldos
      </Typography.Title>

      <Card size="small" title="Filtros">
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
          <Select
            placeholder="Produto"
            value={productId || undefined}
            onChange={(v) => {
              setProductId(v ?? "");
              setPage(1);
            }}
            allowClear
            showSearch
            optionFilterProp="label"
            style={{ width: 280 }}
            options={products.map((p) => ({
              value: String(p.id),
              label: `${p.sku} — ${p.name}`,
            }))}
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
        <Table<StockBalanceRow> rowKey="id" columns={columns} dataSource={list} pagination={false} />
        <PaginationBar page={page} totalCount={count} pageSize={PAGE_SIZE} onPageChange={setPage} />
      </Spin>
    </Space>
  );
}
