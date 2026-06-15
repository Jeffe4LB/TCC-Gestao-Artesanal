import { useCallback, useEffect, useMemo, useState } from "react";
import { Alert, DatePicker, Select, Space, Spin, Table } from "antd";
import dayjs from "dayjs";
import { listarTodosProdutos } from "../../api/cadastro";
import {
  buscarRelatorioMovimentacoesEstoque,
  exportarRelatorioMovimentacoesEstoque,
} from "../../api/relatorios";
import { LayoutRelatorio } from "../../components/relatorios/LayoutRelatorio";
import { ResumoRelatorio } from "../../components/relatorios/ResumoRelatorio";
import type { Produto } from "../../types/cadastro";
import type {
  FormatoExportacao,
  LinhaMovimentacaoEstoqueRelatorio,
  RelatorioMovimentacoesEstoque,
} from "../../types/relatorios";
import { firstDayOfMonthLocal, todayLocal } from "./intervaloDatas";
import type { ColumnsType } from "antd/es/table";
import {
  OPCOES_FILTRO_TIPO_MOVIMENTACAO,
  rotuloTipoMovimentacao,
} from "../../constants/tiposMovimentacaoEstoque";
import { formatBalanceDisplay } from "../../utils/exibicaoQuantidade";

export function RelatorioMovimentacoesEstoquePage() {
  const [from, setFrom] = useState(firstDayOfMonthLocal);
  const [to, setTo] = useState(todayLocal);
  const [product, setProduto] = useState("");
  const [tipoMovimentacao, setMovementType] = useState("");
  const [products, setProdutos] = useState<Produto[]>([]);
  const [data, setData] = useState<RelatorioMovimentacoesEstoque | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    void listarTodosProdutos({ ativo: true }).then(setProdutos).catch(() => {});
  }, []);

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const res = await buscarRelatorioMovimentacoesEstoque({
        from,
        to,
        produto: product ? Number(product) : undefined,
        tipo_movimentacao: tipoMovimentacao || undefined,
        limit: 500,
      });
      setData(res);
    } catch (e) {
      setData(null);
      setErr(e instanceof Error ? e.message : "Erro ao gerar");
    } finally {
      setLoading(false);
    }
  }, [from, to, product, tipoMovimentacao]);

  useEffect(() => {
    void load();
  }, [load]);

  const exportar = async (formato: FormatoExportacao) => {
    setExporting(true);
    setErr(null);
    try {
      await exportarRelatorioMovimentacoesEstoque(formato, {
        from,
        to,
        produto: product ? Number(product) : undefined,
        tipo_movimentacao: tipoMovimentacao || undefined,
        limit: 10000,
      });
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao exportar");
    } finally {
      setExporting(false);
    }
  };

  const columns: ColumnsType<LinhaMovimentacaoEstoqueRelatorio> = useMemo(
    () => [
      {
        title: "Data",
        dataIndex: "criado_em",
        key: "criado_em",
        render: (v: string) => new Date(v).toLocaleString(),
      },
      { title: "Código (SKU)", dataIndex: "sku", key: "sku" },
      { title: "Produto", dataIndex: "nome_produto", key: "nome_produto" },
      {
        title: "Variação (base)",
        dataIndex: "delta_quantidade",
        key: "delta_quantidade",
        align: "right",
        render: (v: string, r: LinhaMovimentacaoEstoqueRelatorio) =>
          formatBalanceDisplay(v, r.unidade_base),
      },
      {
        title: "Tipo",
        dataIndex: "tipo_movimentacao",
        key: "tipo_movimentacao",
        render: (c: string) => rotuloTipoMovimentacao(c),
      },
      {
        title: "Responsável",
        dataIndex: "criado_por_nome",
        key: "criado_por_nome",
        width: 120,
        render: (v: string | null | undefined) => v ?? "—",
      },
      {
        title: "Obs.",
        dataIndex: "observacoes",
        key: "observacoes",
        render: (v) => v || "—",
      },
    ],
    [],
  );

  const resumoItens = useMemo(() => {
    if (!data?.resumo) return [];
    const itens = [
      {
        key: "total",
        titulo: "Movimentações no período",
        valor: data.resumo.total_no_periodo,
      },
      {
        key: "previa",
        titulo: "Linhas na prévia",
        valor: data.total,
      },
    ];
    for (const [tipo, qtd] of Object.entries(data.resumo.contagem_por_tipo)) {
      itens.push({
        key: tipo,
        titulo: rotuloTipoMovimentacao(tipo),
        valor: qtd,
      });
    }
    return itens;
  }, [data]);

  return (
    <LayoutRelatorio
      titulo="Movimentações de estoque"
      descricao="Período pela data do lançamento (campo criado em). A prévia mostra até 500 linhas; a exportação inclui até 10 mil."
      periodo={data ? `${data.de} a ${data.ate}` : undefined}
      filtros={
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
            onChange={(v) => setProduto(v ?? "")}
            allowClear
            showSearch
            optionFilterProp="label"
            style={{ width: 280 }}
            options={products.map((p) => ({
              value: String(p.id),
              label: `${p.sku} — ${p.nome}`,
            }))}
          />
          <Select
            placeholder="Tipo"
            value={tipoMovimentacao || undefined}
            onChange={(v) => setMovementType(v ?? "")}
            allowClear
            style={{ width: 240 }}
            options={[...OPCOES_FILTRO_TIPO_MOVIMENTACAO]}
          />
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
            {data.resumo?.truncado ? (
              <Alert
                type="warning"
                showIcon
                style={{ marginBottom: 16 }}
                message={`Há ${data.resumo.total_no_periodo} movimentações no período; a prévia mostra apenas ${data.resumo.limite_previa}. Use Exportar para a lista completa (até 10 mil).`}
              />
            ) : null}
            {data.resumo ? <ResumoRelatorio itens={resumoItens} /> : null}
            <Table<LinhaMovimentacaoEstoqueRelatorio>
              rowKey="id"
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
