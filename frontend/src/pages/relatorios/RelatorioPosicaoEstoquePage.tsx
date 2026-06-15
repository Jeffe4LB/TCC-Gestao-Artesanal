import { useCallback, useEffect, useMemo, useState } from "react";
import { Button, Input, Select, Space, Spin, Table } from "antd";
import { listarTodasCategorias } from "../../api/cadastro";
import {
  buscarRelatorioPosicaoEstoque,
  exportarRelatorioPosicaoEstoque,
} from "../../api/relatorios";
import { LayoutRelatorio } from "../../components/relatorios/LayoutRelatorio";
import { ResumoRelatorio } from "../../components/relatorios/ResumoRelatorio";
import type { Categoria } from "../../types/cadastro";
import type {
  FormatoExportacao,
  LinhaPosicaoEstoque,
  RelatorioPosicaoEstoque,
} from "../../types/relatorios";
import type { ColumnsType } from "antd/es/table";
import {
  formatBalanceDisplay,
  formatQuantityDisplay,
} from "../../utils/exibicaoQuantidade";

export function RelatorioPosicaoEstoquePage() {
  const [categories, setCategories] = useState<Categoria[]>([]);
  const [category, setCategoria] = useState("");
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [data, setData] = useState<RelatorioPosicaoEstoque | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    void listarTodasCategorias().then(setCategories).catch(() => {});
  }, []);

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const res = await buscarRelatorioPosicaoEstoque({
        categoria: category || undefined,
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

  const exportar = async (formato: FormatoExportacao) => {
    setExporting(true);
    setErr(null);
    try {
      await exportarRelatorioPosicaoEstoque(formato, {
        categoria: category || undefined,
        search: search || undefined,
      });
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao exportar");
    } finally {
      setExporting(false);
    }
  };

  const columns: ColumnsType<LinhaPosicaoEstoque> = useMemo(
    () => [
      { title: "Código (SKU)", dataIndex: "sku", key: "sku" },
      { title: "Nome", dataIndex: "nome", key: "nome" },
      { title: "Categoria", dataIndex: "categoria", key: "categoria", render: (v) => v || "—" },
      {
        title: "Saldo (base)",
        dataIndex: "quantidade",
        key: "quantidade",
        align: "right",
        render: (v: string, r: LinhaPosicaoEstoque) =>
          formatBalanceDisplay(v, r.unidade_base),
      },
      {
        title: "Mín.",
        dataIndex: "estoque_minimo",
        key: "estoque_minimo",
        align: "right",
        render: (v: string) => formatQuantityDisplay(v),
      },
      {
        title: "Abaixo?",
        dataIndex: "abaixo_minimo",
        key: "abaixo_minimo",
        render: (v: boolean) => (v ? "Sim" : "Não"),
      },
    ],
    [],
  );

  return (
    <LayoutRelatorio
      titulo="Posição de estoque"
      descricao="Saldos ativos por produto. O valor estimado usa quantidade × custo unitário do cadastro."
      periodo={data ? `${data.total} SKU(s) listado(s)` : undefined}
      filtros={
        <Space wrap>
          <Select
            placeholder="Categoria"
            value={category || undefined}
            onChange={(v) => setCategoria(v ?? "")}
            allowClear
            style={{ width: 220 }}
            options={categories.map((c) => ({ value: String(c.id), label: c.nome }))}
          />
          <Input
            placeholder="Buscar código ou nome"
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
      }
      onAtualizar={() => void load()}
      onExportarFormato={exportar}
      loadingAtualizar={loading}
      loadingExportar={exporting}
      textoAtualizar="Atualizar prévia"
      erro={err}
    >
      <Spin spinning={loading && !data}>
        {data ? (
          <>
            {data.resumo ? (
              <ResumoRelatorio
                itens={[
                  { key: "skus", titulo: "SKUs", valor: data.resumo.total_skus },
                  {
                    key: "valor",
                    titulo: "Valor estoque (est.)",
                    valor: data.resumo.valor_estoque,
                    prefixo: "R$ ",
                  },
                ]}
              />
            ) : null}
            <Table<LinhaPosicaoEstoque>
              rowKey="sku"
              columns={columns}
              dataSource={data.resultados}
              pagination={false}
              size="small"
              scroll={{ x: "max-content" }}
            />
          </>
        ) : null}
      </Spin>
    </LayoutRelatorio>
  );
}
