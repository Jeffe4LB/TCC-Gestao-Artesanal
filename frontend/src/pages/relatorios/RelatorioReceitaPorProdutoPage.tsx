import { useCallback, useEffect, useMemo, useState } from "react";
import { DatePicker, Select, Space, Spin, Table, Typography } from "antd";
import dayjs from "dayjs";
import { listarTodasCategorias, listarTodosClientes } from "../../api/cadastro";
import {
  buscarRelatorioReceitaPorProduto,
  exportarRelatorioReceitaPorProduto,
} from "../../api/relatorios";
import { LayoutRelatorio } from "../../components/relatorios/LayoutRelatorio";
import { ResumoRelatorio } from "../../components/relatorios/ResumoRelatorio";
import { RodapeTotaisTabela } from "../../components/relatorios/RodapeTotaisTabela";
import type { Categoria, Cliente } from "../../types/cadastro";
import type {
  FormatoExportacao,
  LinhaReceitaPorProduto,
  RelatorioReceitaPorProduto,
} from "../../types/relatorios";
import type { ColumnsType } from "antd/es/table";
import { formatQuantityDisplay } from "../../utils/exibicaoQuantidade";
import { firstDayOfMonthLocal, todayLocal } from "./intervaloDatas";

export function RelatorioReceitaPorProdutoPage() {
  const [from, setFrom] = useState(firstDayOfMonthLocal);
  const [to, setTo] = useState(todayLocal);
  const [customerId, setClienteId] = useState<number | undefined>(undefined);
  const [categoryId, setCategoriaId] = useState<number | undefined>(undefined);
  const [customers, setClientes] = useState<Cliente[]>([]);
  const [categories, setCategories] = useState<Categoria[]>([]);
  const [data, setData] = useState<RelatorioReceitaPorProduto | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    void Promise.all([listarTodosClientes(), listarTodasCategorias()])
      .then(([cust, cats]) => {
        setClientes(cust);
        setCategories(cats);
      })
      .catch(() => {});
  }, []);

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const res = await buscarRelatorioReceitaPorProduto({
        from,
        to,
        cliente: customerId,
        categoria: categoryId,
      });
      setData(res);
    } catch (e) {
      setData(null);
      setErr(e instanceof Error ? e.message : "Erro ao gerar");
    } finally {
      setLoading(false);
    }
  }, [from, to, customerId, categoryId]);

  useEffect(() => {
    void load();
  }, [load]);

  const exportar = async (formato: FormatoExportacao) => {
    setExporting(true);
    setErr(null);
    try {
      await exportarRelatorioReceitaPorProduto(formato, {
        from,
        to,
        cliente: customerId,
        categoria: categoryId,
      });
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao exportar");
    } finally {
      setExporting(false);
    }
  };

  const columns: ColumnsType<LinhaReceitaPorProduto> = useMemo(
    () => [
      { title: "Código (SKU)", dataIndex: "sku", key: "sku", width: 110 },
      { title: "Produto", dataIndex: "nome", key: "nome" },
      {
        title: "Categoria",
        dataIndex: "categoria",
        key: "categoria",
        width: 140,
        render: (v: string) => v || "—",
      },
      {
        title: "Qtd vendida",
        dataIndex: "quantidade",
        key: "quantidade",
        align: "right",
        render: (v: string) => formatQuantityDisplay(v),
      },
      {
        title: "Faturamento (R$)",
        dataIndex: "faturamento_total",
        key: "faturamento_total",
        align: "right",
      },
      { title: "Custo (R$)", dataIndex: "custo_total", key: "custo_total", align: "right" },
      { title: "Margem (R$)", dataIndex: "lucro", key: "lucro", align: "right" },
      {
        title: "Margem %",
        dataIndex: "margem_percentual",
        key: "margem_percentual",
        align: "right",
        render: (v: string) => `${v}%`,
      },
    ],
    [],
  );

  const resumoItens = data?.resumo
    ? [
        {
          key: "fat",
          titulo: "Faturamento",
          valor: data.resumo.faturamento_total,
          prefixo: "R$ ",
        },
        {
          key: "custo",
          titulo: "Custo",
          valor: data.resumo.custo_total,
          prefixo: "R$ ",
        },
        {
          key: "lucro",
          titulo: "Lucro líquido",
          valor: data.resumo.lucro_total,
          prefixo: "R$ ",
        },
        {
          key: "margem",
          titulo: "Margem média",
          valor: data.resumo.margem_percentual,
          sufixo: "%",
        },
      ]
    : [];

  return (
    <LayoutRelatorio
      titulo="Receita por produto"
      descricao="Relatório de Custo e Receita por Produto"
      periodo={data ? `Período: ${data.de} a ${data.ate} — ${data.total} produto(s) com movimento` : undefined}
      filtros={
        <Space wrap>
          <DatePicker
            format="YYYY-MM-DD"
            value={dayjs(from)}
            onChange={(_, s) => setFrom(typeof s === "string" && s ? s : firstDayOfMonthLocal())}
          />
          <DatePicker
            format="YYYY-MM-DD"
            value={dayjs(to)}
            onChange={(_, s) => setTo(typeof s === "string" && s ? s : todayLocal())}
          />
          <Select
            placeholder="Cliente"
            allowClear
            style={{ width: 240 }}
            value={customerId}
            onChange={(v) => setClienteId(v)}
            options={customers.map((c) => ({ value: c.id, label: c.nome }))}
          />
          <Select
            placeholder="Categoria"
            allowClear
            style={{ width: 200 }}
            value={categoryId}
            onChange={(v) => setCategoriaId(v)}
            options={categories.map((c) => ({ value: c.id, label: c.nome }))}
          />
        </Space>
      }
      onAtualizar={() => void load()}
      onExportarFormato={exportar}
      loadingAtualizar={loading}
      loadingExportar={exporting}
      erro={err}
    >
      <Spin spinning={loading && !data}>
        {data ? (
          <>
            {data.resumo ? <ResumoRelatorio itens={resumoItens} /> : null}
            <Table<LinhaReceitaPorProduto>
              rowKey="id_produto"
              columns={columns}
              dataSource={data.resultados}
              pagination={false}
              size="small"
              scroll={{ x: "max-content" }}
              summary={() =>
                data.resumo ? (
                  <RodapeTotaisTabela
                    celulas={[
                      { conteudo: <Typography.Text strong>Totais</Typography.Text> },
                      { conteudo: null },
                      { conteudo: null },
                      { conteudo: null, alinhar: "right" },
                      {
                        conteudo: (
                          <Typography.Text strong>{data.resumo!.faturamento_total}</Typography.Text>
                        ),
                        alinhar: "right",
                      },
                      {
                        conteudo: (
                          <Typography.Text strong>{data.resumo!.custo_total}</Typography.Text>
                        ),
                        alinhar: "right",
                      },
                      {
                        conteudo: (
                          <Typography.Text strong>{data.resumo!.lucro_total}</Typography.Text>
                        ),
                        alinhar: "right",
                      },
                      {
                        conteudo: (
                          <Typography.Text strong>{data.resumo!.margem_percentual}%</Typography.Text>
                        ),
                        alinhar: "right",
                      },
                    ]}
                  />
                ) : null
              }
            />
          </>
        ) : null}
      </Spin>
    </LayoutRelatorio>
  );
}
