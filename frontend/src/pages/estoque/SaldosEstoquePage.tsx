import { useCallback, useEffect, useMemo, useState } from "react";
import { Alert, Button, Card, Input, Select, Space, Spin, Table, Typography } from "antd";
import { BarraPaginacao } from "../../components/BarraPaginacao";
import { listarTodosProdutos } from "../../api/cadastro";
import { listarSaldosEstoque } from "../../api/estoque";
import type { Produto } from "../../types/cadastro";
import type { SaldoEstoque } from "../../types/estoque";
import type { ColumnsType } from "antd/es/table";
import { formatBalanceDisplay } from "../../utils/exibicaoQuantidade";

const PAGE_SIZE = 20;

export function SaldosEstoquePage() {
  const [list, setList] = useState<SaldoEstoque[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [produtoId, setProdutoId] = useState<string>("");
  const [products, setProdutos] = useState<Produto[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    void listarTodosProdutos({ ativo: true }).then(setProdutos).catch(() => {});
  }, []);

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const data = await listarSaldosEstoque({
        page,
        search: search || undefined,
        produto: produtoId || undefined,
        ordering: "produto__nome",
      });
      setList(data.resultados);
      setCount(data.total);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao listar");
    } finally {
      setLoading(false);
    }
  }, [page, search, produtoId]);

  useEffect(() => {
    void load();
  }, [load]);

  const columns: ColumnsType<SaldoEstoque> = useMemo(
    () => [
      { title: "Código (SKU)", dataIndex: "codigo_produto", key: "codigo_produto" },
      { title: "Produto", dataIndex: "nome_produto", key: "nome_produto" },
      {
        title: "Saldo (base)",
        key: "qty_base",
        render: (_: unknown, r: SaldoEstoque) =>
          formatBalanceDisplay(r.quantidade, r.unidade_base),
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
            placeholder="Buscar código ou nome"
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
            value={produtoId || undefined}
            onChange={(v) => {
              setProdutoId(v ?? "");
              setPage(1);
            }}
            allowClear
            showSearch
            optionFilterProp="label"
            style={{ width: 280 }}
            options={products.map((p) => ({
              value: String(p.id),
              label: `${p.sku} — ${p.nome}`,
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
        <Table<SaldoEstoque> rowKey="id" columns={columns} dataSource={list} pagination={false} />
        <BarraPaginacao page={page} totalCount={count} pageSize={PAGE_SIZE} onPageChange={setPage} />
      </Spin>
    </Space>
  );
}
