import { useCallback, useEffect, useMemo, useState } from "react";
import { Alert, Button, Card, Input, Space, Spin, Table, Typography } from "antd";
import { BarraPaginacao } from "../../components/BarraPaginacao";
import { listarAlertasEstoque } from "../../api/estoque";
import type { AlertaEstoqueBaixo } from "../../types/estoque";
import type { ColumnsType } from "antd/es/table";
import {
  formatBalanceDisplay,
  formatQuantityDisplay,
} from "../../utils/exibicaoQuantidade";

const PAGE_SIZE = 20;

export function AlertasEstoquePage() {
  const [list, setList] = useState<AlertaEstoqueBaixo[]>([]);
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
      const data = await listarAlertasEstoque({
        page,
        search: search || undefined,
      });
      setList(data.resultados);
      setCount(data.total);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao listar");
    } finally {
      setLoading(false);
    }
  }, [page, search]);

  useEffect(() => {
    void load();
  }, [load]);

  const columns: ColumnsType<AlertaEstoqueBaixo> = useMemo(
    () => [
      { title: "Código (SKU)", dataIndex: "codigo", key: "codigo" },
      { title: "Produto", dataIndex: "nome", key: "nome" },
      {
        title: "Mínimo",
        dataIndex: "estoque_minimo",
        key: "estoque_minimo",
        render: (v: string) => formatQuantityDisplay(v),
      },
      {
        title: "Atual (base)",
        dataIndex: "quantidade_atual",
        key: "quantidade_atual",
        render: (v: string, r: AlertaEstoqueBaixo) =>
          formatBalanceDisplay(v, r.unidade_base),
      },
      {
        title: "Falta (base)",
        dataIndex: "deficit",
        key: "deficit",
        render: (v: string, r: AlertaEstoqueBaixo) => formatBalanceDisplay(v, r.unidade_base),
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
        <Table<AlertaEstoqueBaixo>
          rowKey="id_produto"
          columns={columns}
          dataSource={list}
          pagination={false}
        />
        <BarraPaginacao page={page} totalCount={count} pageSize={PAGE_SIZE} onPageChange={setPage} />
      </Spin>
    </Space>
  );
}
