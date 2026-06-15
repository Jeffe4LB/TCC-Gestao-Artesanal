import { useCallback, useEffect, useMemo, useState } from "react";
import {
  coerceProductUnitCode,
  compatibleUnitsForProduct,
  PRODUCT_UNIT_OPTIONS,
} from "../../constants/unidades";
import type { ProductUnitCode } from "../../constants/unidades";
import { Link } from "react-router-dom";
import { StopOutlined } from "@ant-design/icons";
import { Alert, Button, Card, Input, Popconfirm, Select, Space, Spin, Table, Tag, Tooltip, Typography } from "antd";
import { FormularioNovaOrdemProducao } from "../../components/estoque/producao/FormularioNovaOrdemProducao";
import { BarraPaginacao } from "../../components/BarraPaginacao";
import { listarTodosProdutos } from "../../api/cadastro";
import {
  cancelarOrdemProducao,
  criarOrdemProducao,
  obterReceita,
  listarOrdensProducao,
  listarReceitas,
} from "../../api/estoque";
import type { Produto } from "../../types/cadastro";
import type { OrdemProducao, Receita } from "../../types/estoque";
import type { ColumnsType } from "antd/es/table";
import { formatQuantityDisplay } from "../../utils/exibicaoQuantidade";
import { estimarPreviaCustoProducao } from "../../utils/previaCustoProducao";
import { montarLinhasProducaoDaReceita } from "../../utils/preenchimentoReceitaProducao";

const PAGE_SIZE = 20;

type LineForm = { insumo: string; quantidade_consumida: string; quantidade_consumida_unidade: ProductUnitCode | "" };

const emptyLine = (): LineForm => ({ insumo: "", quantidade_consumida: "", quantidade_consumida_unidade: "" });

export function OrdensProducaoPage() {
  const [list, setList] = useState<OrdemProducao[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [filterProduto, setFilterProduto] = useState<string>("");
  const [filterSituacao, setFilterSituacao] = useState<"" | "ativas" | "canceladas">("");
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const [productsMfg, setProdutosMfg] = useState<Produto[]>([]);
  const [productsAll, setProdutosAll] = useState<Produto[]>([]);

  const [formProduto, setFormProduto] = useState("");
  const [formQty, setFormQty] = useState("");
  const [formQtyUnit, setFormQtyUnit] = useState<ProductUnitCode>("UN");
  const [formNotes, setFormNotes] = useState("");
  const [formLines, setFormLines] = useState<LineForm[]>([emptyLine()]);
  const [recipeSnapshot, setReceitaSnapshot] = useState<Receita | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    void (async () => {
      try {
        const [mfg, all] = await Promise.all([
          listarTodosProdutos({ tipo_produto: "fabricado", ativo: true }),
          listarTodosProdutos({ ativo: true }),
        ]);
        setProdutosMfg(mfg);
        setProdutosAll(all);
      } catch {
        /* */
      }
    })();
  }, []);

  useEffect(() => {
    const p = productsMfg.find((x) => String(x.id) === formProduto);
    if (p) {
      // Unidade de cadastro (ex.: ML, G): alinha com custo unitário do produto, que é por 1 unidade de cadastro.
      setFormQtyUnit(coerceProductUnitCode(p.unidade));
    }
  }, [formProduto, productsMfg]);

  const producedUnitOptions = useMemo(() => {
    const p = productsMfg.find((x) => String(x.id) === formProduto);
    if (!p) return PRODUCT_UNIT_OPTIONS;
    const codes = compatibleUnitsForProduct(coerceProductUnitCode(p.unidade));
    return PRODUCT_UNIT_OPTIONS.filter((o) => codes.includes(o.value));
  }, [formProduto, productsMfg]);

  useEffect(() => {
    setReceitaSnapshot(null);
    if (!formProduto || !productsAll.length) {
      return;
    }
    setFormLines([emptyLine()]);
    let cancelled = false;
    void (async () => {
      try {
        const res = await listarReceitas({ produto: Number(formProduto), page: 1 });
        if (cancelled) return;
        if (!res.resultados.length) {
          setReceitaSnapshot(null);
          return;
        }
        const recipe = await obterReceita(res.resultados[0].id);
        if (!cancelled) setReceitaSnapshot(recipe);
      } catch {
        if (!cancelled) setReceitaSnapshot(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [formProduto, productsAll]);

  useEffect(() => {
    if (!formProduto) {
      setFormLines([emptyLine()]);
      return;
    }
    if (!recipeSnapshot || String(recipeSnapshot.produto) !== formProduto) {
      return;
    }
    const finished = productsMfg.find((p) => String(p.id) === formProduto);
    if (!finished) return;
    const map = new Map(productsAll.map((p) => [p.id, p]));
    setFormLines(montarLinhasProducaoDaReceita(recipeSnapshot, finished, map, formQty, formQtyUnit));
  }, [recipeSnapshot, formProduto, formQty, formQtyUnit, productsMfg, productsAll]);

  const unitOptionsForComponent = useCallback((componentId: string) => {
    const p = productsAll.find((x) => String(x.id) === componentId);
    if (!p) return PRODUCT_UNIT_OPTIONS;
    const codes = compatibleUnitsForProduct(coerceProductUnitCode(p.unidade));
    return PRODUCT_UNIT_OPTIONS.filter((o) => codes.includes(o.value));
  }, [productsAll]);

  const costPreview = useMemo(
    () =>
      estimarPreviaCustoProducao({
        producedProduto: productsMfg.find((p) => String(p.id) === formProduto),
        qtyProducedStr: formQty,
        qtyProducedUnit: formQtyUnit,
        linhas: formLines,
        componentsCatalog: productsAll,
      }),
    [formProduto, formQty, formQtyUnit, formLines, productsMfg, productsAll],
  );

  const finishedProduto = useMemo(
    () => productsMfg.find((p) => String(p.id) === formProduto),
    [formProduto, productsMfg],
  );

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const data = await listarOrdensProducao({
        page,
        search: search || undefined,
        produto: filterProduto || undefined,
        ativa:
          filterSituacao === "ativas" ? true : filterSituacao === "canceladas" ? false : undefined,
        ordering: "-criado_em",
      });
      setList(data.resultados);
      setCount(data.total);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao listar");
    } finally {
      setLoading(false);
    }
  }, [page, search, filterProduto, filterSituacao]);

  const handleCancelar = useCallback(async (run: OrdemProducao) => {
    setErr(null);
    try {
      await cancelarOrdemProducao(run.id);
      await load();
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Erro ao cancelar produção");
    }
  }, [load]);

  useEffect(() => {
    void load();
  }, [load]);

  const buildLinesPayload = (): Array<{
    insumo: number;
    quantidade_consumida: string;
    quantidade_consumida_unidade?: string;
  }> => {
    const out: Array<{
      insumo: number;
      quantidade_consumida: string;
      quantidade_consumida_unidade?: string;
    }> = [];
    for (const row of formLines) {
      if (!row.insumo.trim() || !row.quantidade_consumida.trim()) continue;
      const line: {
        insumo: number;
        quantidade_consumida: string;
        quantidade_consumida_unidade?: string;
      } = {
        insumo: Number(row.insumo),
        quantidade_consumida: row.quantidade_consumida.trim(),
      };
      if (row.quantidade_consumida_unidade) {
        line.quantidade_consumida_unidade = row.quantidade_consumida_unidade;
      }
      out.push(line);
    }
    return out;
  };

  const resetForm = () => {
    setFormProduto("");
    setFormQty("");
    setFormQtyUnit("UN");
    setFormNotes("");
    setReceitaSnapshot(null);
    setFormLines([emptyLine()]);
  };

  const submitForm = async () => {
    const linesPayload = buildLinesPayload();
    if (!formProduto) {
      setErr("Selecione o produto fabricado.");
      return;
    }
    const qtyNorm = String(formQty).trim().replace(",", ".");
    const qtyNum = Number(qtyNorm);
    if (!Number.isFinite(qtyNum) || qtyNum <= 0) {
      setErr("Informe a quantidade produzida (número maior que zero).");
      return;
    }
    if (!linesPayload.length) {
      setErr("Informe ao menos uma linha de consumo de insumo.");
      return;
    }
    setSaving(true);
    setErr(null);
    try {
      await criarOrdemProducao({
        produto: Number(formProduto),
        quantidade_produzida: qtyNorm,
        quantidade_produzida_unidade: formQtyUnit,
        linhas: linesPayload,
        observacoes: formNotes.trim() || undefined,
      });
      resetForm();
      await load();
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Erro ao registrar produção");
    } finally {
      setSaving(false);
    }
  };

  const addLine = () => setFormLines((rows) => [...rows, emptyLine()]);
  const removeLine = (index: number) =>
    setFormLines((rows) => rows.filter((_, i) => i !== index));

  const updateLine = (index: number, patch: Partial<LineForm>) =>
    setFormLines((rows) =>
      rows.map((row, i) => (i === index ? { ...row, ...patch } : row)),
    );

  const columns: ColumnsType<OrdemProducao> = useMemo(
    () => [
      {
        title: "Data",
        dataIndex: "criado_em",
        key: "criado_em",
        render: (v: string) => new Date(v).toLocaleString(),
      },
      {
        title: "Produto",
        key: "product",
        render: (_, run) => `${run.codigo_produto} — ${run.nome_produto}`,
      },
      {
        title: "Qtd",
        dataIndex: "quantidade_produzida",
        key: "quantidade_produzida",
        render: (v: string) => formatQuantityDisplay(v),
      },
      {
        title: "Situação",
        key: "situacao",
        render: (_, run) =>
          run.cancelada_em ? (
            <Tag color="default">Cancelada</Tag>
          ) : (
            <Tag color="success">Ativa</Tag>
          ),
      },
      {
        title: "Ações",
        key: "actions",
        width: 120,
        render: (_, run) => (
          <Space size={4}>
            <Link to={`/app/estoque/producao/${run.id}`}>
              <Typography.Link>Ver</Typography.Link>
            </Link>
            {!run.cancelada_em ? (
              <Popconfirm
                title="Cancelar esta produção?"
                description="O estoque será estornado. O registro permanece no histórico."
                okText="Cancelar produção"
                cancelText="Voltar"
                okButtonProps={{ danger: true }}
                onConfirm={() => void handleCancelar(run)}
              >
                <Tooltip title="Cancelar produção">
                  <Button
                    type="text"
                    danger
                    icon={<StopOutlined />}
                    aria-label="Cancelar produção"
                  />
                </Tooltip>
              </Popconfirm>
            ) : null}
          </Space>
        ),
      },
    ],
    [handleCancelar],
  );

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Typography.Title level={3} style={{ margin: 0 }}>
        Produção
      </Typography.Title>

      <Card size="small" title="Filtros">
        <Space wrap>
          <Input
            placeholder="Buscar código ou observações"
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
            value={filterProduto || undefined}
            onChange={(v) => {
              setFilterProduto(v ?? "");
              setPage(1);
            }}
            allowClear
            showSearch
            optionFilterProp="label"
            style={{ width: 280 }}
            options={productsMfg.map((p) => ({
              value: String(p.id),
              label: `${p.sku} — ${p.nome}`,
            }))}
          />
          <Select
            placeholder="Situação"
            value={filterSituacao || undefined}
            onChange={(v) => {
              setFilterSituacao((v ?? "") as "" | "ativas" | "canceladas");
              setPage(1);
            }}
            allowClear
            style={{ width: 140 }}
            options={[
              { value: "ativas", label: "Ativas" },
              { value: "canceladas", label: "Canceladas" },
            ]}
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

      <FormularioNovaOrdemProducao
        productsMfg={productsMfg}
        productsAll={productsAll}
        formProduto={formProduto}
        onFormProdutoChange={setFormProduto}
        formQty={formQty}
        onFormQtyChange={setFormQty}
        formQtyUnit={formQtyUnit}
        onFormQtyUnitChange={setFormQtyUnit}
        producedUnitOptions={producedUnitOptions}
        formNotes={formNotes}
        onFormNotesChange={setFormNotes}
        formLines={formLines}
        onAddLine={addLine}
        onRemoveLine={removeLine}
        onUpdateLine={updateLine}
        unitOptionsForComponent={unitOptionsForComponent}
        costPreview={costPreview}
        finishedProduto={finishedProduto}
        saving={saving}
        onSubmit={() => void submitForm()}
        onReset={resetForm}
      />

      {err ? <Alert type="error" message={err} showIcon /> : null}

      <Spin spinning={loading}>
        <Table<OrdemProducao> rowKey="id" columns={columns} dataSource={list} pagination={false} />
        <BarraPaginacao page={page} totalCount={count} pageSize={PAGE_SIZE} onPageChange={setPage} />
      </Spin>
    </Space>
  );
}
