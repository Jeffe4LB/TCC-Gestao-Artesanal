import { useCallback, useEffect, useMemo, useState } from "react";
import { Button, Form, Input, Spin, Table } from "antd";
import {
  buscarRelatorioEstoqueAbaixoMinimo,
  exportarRelatorioEstoqueAbaixoMinimo,
} from "../../api/relatorios";
import { LayoutRelatorio } from "../../components/relatorios/LayoutRelatorio";
import { ResumoRelatorio } from "../../components/relatorios/ResumoRelatorio";
import type {
  FormatoExportacao,
  LinhaEstoqueAbaixoMinimo,
  RelatorioEstoqueAbaixoMinimo,
} from "../../types/relatorios";
import type { ColumnsType } from "antd/es/table";
import {
  formatBalanceDisplay,
  formatQuantityDisplay,
} from "../../utils/exibicaoQuantidade";

export function RelatorioEstoqueAbaixoMinimoPage() {
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [data, setData] = useState<RelatorioEstoqueAbaixoMinimo | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const res = await buscarRelatorioEstoqueAbaixoMinimo({
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

  const exportar = async (formato: FormatoExportacao) => {
    setExporting(true);
    setErr(null);
    try {
      await exportarRelatorioEstoqueAbaixoMinimo(formato, {
        search: search || undefined,
      });
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao exportar");
    } finally {
      setExporting(false);
    }
  };

  const columns: ColumnsType<LinhaEstoqueAbaixoMinimo> = useMemo(
    () => [
      { title: "Código (SKU)", dataIndex: "sku", key: "sku" },
      { title: "Nome", dataIndex: "nome", key: "nome" },
      {
        title: "Mínimo",
        dataIndex: "estoque_minimo",
        key: "estoque_minimo",
        align: "right",
        render: (v: string) => formatQuantityDisplay(v),
      },
      {
        title: "Saldo (base)",
        dataIndex: "quantidade_atual",
        key: "quantidade_atual",
        align: "right",
        render: (v: string, r: LinhaEstoqueAbaixoMinimo) =>
          formatBalanceDisplay(v, r.unidade_base),
      },
      {
        title: "Falta (base)",
        dataIndex: "gap",
        key: "gap",
        align: "right",
        render: (v: string, r: LinhaEstoqueAbaixoMinimo) => formatBalanceDisplay(v, r.unidade_base),
      },
    ],
    [],
  );

  return (
    <LayoutRelatorio
      titulo="Estoque abaixo do mínimo"
      descricao="Produtos com saldo igual ou inferior ao estoque mínimo cadastrado."
      periodo={data ? `${data.total} item(ns) crítico(s)` : undefined}
      filtros={
        <Form layout="inline" onFinish={() => setSearch(searchInput.trim())}>
          <Form.Item>
            <Input
              placeholder="Buscar código ou nome"
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
            <ResumoRelatorio
              itens={[
                {
                  key: "criticos",
                  titulo: "Itens críticos",
                  valor: data.resumo?.itens_criticos ?? data.total,
                },
              ]}
            />
            <Table<LinhaEstoqueAbaixoMinimo>
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
