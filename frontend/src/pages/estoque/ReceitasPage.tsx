import { useCallback, useEffect, useMemo, useState } from "react";
import {
  coerceProductUnitCode,
  compatibleUnitsForProduct,
  PRODUCT_UNIT_OPTIONS,
} from "../../constants/unidades";
import type { ProductUnitCode } from "../../constants/unidades";
import {
  Alert,
  Button,
  Card,
  Form,
  Input,
  Popconfirm,
  Select,
  Space,
  Spin,
  Table,
  theme,
  Tooltip,
  Typography,
} from "antd";
import { DeleteOutlined, EditOutlined, PlusOutlined } from "@ant-design/icons";
import { BarraPaginacao } from "../../components/BarraPaginacao";
import { listarTodosProdutos } from "../../api/cadastro";
import {
  criarReceita,
  excluirReceita,
  obterReceita,
  listarReceitas,
  atualizarReceita,
} from "../../api/estoque";
import type { Produto } from "../../types/cadastro";
import type { Receita, LinhaReceita } from "../../types/estoque";
import type { ColumnsType } from "antd/es/table";
import {
  estimarPreviaCustoProducao,
  formatarBRL,
  unitLabel,
} from "../../utils/previaCustoProducao";

const PAGE_SIZE = 20;

type LineForm = {
  insumo: string;
  quantidade_por_unidade: string;
  quantidade_por_unidade_unidade: ProductUnitCode | "";
};

const emptyLine = (): LineForm => ({
  insumo: "",
  quantidade_por_unidade: "",
  quantidade_por_unidade_unidade: "",
});

export function ReceitasPage() {
  const { token } = theme.useToken();
  const [list, setList] = useState<Receita[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [filterProduto, setFilterProduto] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const [productsMfg, setProdutosMfg] = useState<Produto[]>([]);
  const [productsAll, setProdutosAll] = useState<Produto[]>([]);

  const [editing, setEditing] = useState<Receita | null>(null);
  const [formProduto, setFormProduto] = useState("");
  const [formNotes, setFormNotes] = useState("");
  const [formLines, setFormLines] = useState<LineForm[]>([emptyLine()]);
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
        /* selects vazios */
      }
    })();
  }, []);

  const productById = useCallback(
    (id: number) => productsAll.find((p) => p.id === id),
    [productsAll],
  );

  const unitOptionsForComponent = useCallback(
    (componentId: string) => {
      const p = productsAll.find((x) => String(x.id) === componentId);
      if (!p) return PRODUCT_UNIT_OPTIONS;
      const codes = compatibleUnitsForProduct(coerceProductUnitCode(p.unidade));
      return PRODUCT_UNIT_OPTIONS.filter((o) => codes.includes(o.value));
    },
    [productsAll],
  );

  const finishedProdutoId = editing ? String(editing.produto) : formProduto;
  const finishedProdutoForCost = finishedProdutoId
    ? productsMfg.find((p) => String(p.id) === finishedProdutoId)
    : undefined;

  const linhasPreviaCusto = useMemo(
    () =>
      formLines.map((row) => ({
        insumo: row.insumo,
        quantidade_consumida: row.quantidade_por_unidade,
        quantidade_consumida_unidade: row.quantidade_por_unidade_unidade,
      })),
    [formLines],
  );

  const costPreview = useMemo(() => {
    if (!finishedProdutoForCost) {
      return estimarPreviaCustoProducao({
        producedProduto: undefined,
        qtyProducedStr: "",
        qtyProducedUnit: "UN",
        linhas: linhasPreviaCusto,
        componentsCatalog: productsAll,
      });
    }
    const cat = coerceProductUnitCode(finishedProdutoForCost.unidade);
    return estimarPreviaCustoProducao({
      producedProduto: finishedProdutoForCost,
      qtyProducedStr: "1",
      qtyProducedUnit: cat,
      linhas: linhasPreviaCusto,
      componentsCatalog: productsAll,
    });
  }, [finishedProdutoForCost, linhasPreviaCusto, productsAll]);

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const data = await listarReceitas({
        page,
        search: search || undefined,
        produto: filterProduto || undefined,
        ordering: "-atualizado_em",
      });
      setList(data.resultados);
      setCount(data.total);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao listar");
    } finally {
      setLoading(false);
    }
  }, [page, search, filterProduto]);

  useEffect(() => {
    void load();
  }, [load]);

  const resetForm = () => {
    setEditing(null);
    setFormProduto("");
    setFormNotes("");
    setFormLines([emptyLine()]);
  };

  const linesFromReceita = (linhas: LinhaReceita[]): LineForm[] =>
    linhas.length
      ? linhas.map((l) => {
          const p = productsAll.find((x) => x.id === l.insumo);
          return {
            insumo: String(l.insumo),
            quantidade_por_unidade: l.quantidade_por_unidade,
            quantidade_por_unidade_unidade: p ? coerceProductUnitCode(p.unidade) : "",
          };
        })
      : [emptyLine()];

  const startEdit = async (r: Receita) => {
    setErr(null);
    try {
      const full = await obterReceita(r.id);
      setEditing(full);
      setFormProduto(String(full.produto));
      setFormNotes(full.observacoes);
      setFormLines(linesFromReceita(full.linhas));
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao carregar receita");
    }
  };

  const buildLinesPayload = (): Array<{
    insumo: number;
    quantidade_por_unidade: string;
    quantidade_por_unidade_unidade?: string;
  }> => {
    const out: Array<{
      insumo: number;
      quantidade_por_unidade: string;
      quantidade_por_unidade_unidade?: string;
    }> = [];
    for (const row of formLines) {
      if (!row.insumo.trim() || !row.quantidade_por_unidade.trim()) continue;
      const line: {
        insumo: number;
        quantidade_por_unidade: string;
        quantidade_por_unidade_unidade?: string;
      } = {
        insumo: Number(row.insumo),
        quantidade_por_unidade: row.quantidade_por_unidade.trim(),
      };
      if (row.quantidade_por_unidade_unidade) {
        line.quantidade_por_unidade_unidade = row.quantidade_por_unidade_unidade;
      }
      out.push(line);
    }
    return out;
  };

  const submitForm = async () => {
    const linesPayload = buildLinesPayload();
    if (!linesPayload.length) {
      setErr("Informe ao menos uma linha de insumo com quantidade.");
      return;
    }
    setSaving(true);
    setErr(null);
    try {
      if (editing) {
        await atualizarReceita(editing.id, {
          observacoes: formNotes.trim(),
          linhas: linesPayload,
        });
      } else {
        if (!formProduto) {
          setErr("Selecione o produto fabricado.");
          setSaving(false);
          return;
        }
        await criarReceita({
          produto: Number(formProduto),
          observacoes: formNotes.trim() || undefined,
          linhas: linesPayload,
        });
      }
      resetForm();
      await load();
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Erro ao salvar");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (r: Receita) => {
    setErr(null);
    try {
      await excluirReceita(r.id);
      if (editing?.id === r.id) resetForm();
      await load();
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Erro ao excluir");
    }
  };

  const addLine = () => setFormLines((rows) => [...rows, emptyLine()]);
  const removeLine = (index: number) =>
    setFormLines((rows) => rows.filter((_, i) => i !== index));

  const updateLine = (index: number, patch: Partial<LineForm>) =>
    setFormLines((rows) =>
      rows.map((row, i) => (i === index ? { ...row, ...patch } : row)),
    );

  const columns: ColumnsType<Receita> = useMemo(
    () => [
      {
        title: "Produto",
        key: "product",
        render: (_, r) => {
          const p = productById(r.produto);
          return p ? `${p.sku} — ${p.nome}` : `#${r.produto}`;
        },
      },
      { title: "Linhas", key: "lines", render: (_, r) => r.linhas?.length ?? 0 },
      {
        title: "Atualizado",
        dataIndex: "atualizado_em",
        key: "atualizado_em",
        render: (v: string) => new Date(v).toLocaleString(),
      },
      {
        title: "Ações",
        key: "actions",
        width: 96,
        render: (_, r) => (
          <Space size={4}>
            <Tooltip title="Editar">
              <Button
                type="text"
                icon={<EditOutlined />}
                aria-label="Editar"
                onClick={() => void startEdit(r)}
              />
            </Tooltip>
            <Tooltip title="Excluir">
              <Popconfirm
                title="Excluir esta receita?"
                okText="Excluir"
                cancelText="Cancelar"
                okButtonProps={{ danger: true }}
                onConfirm={() => void handleDelete(r)}
              >
                <Button type="text" danger icon={<DeleteOutlined />} aria-label="Excluir" />
              </Popconfirm>
            </Tooltip>
          </Space>
        ),
      },
    ],
    [productById],
  );

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Typography.Title level={3} style={{ margin: 0 }}>
        Receitas
      </Typography.Title>

      <Card size="small" title="Filtros">
        <Space wrap>
          <Input
            placeholder="Buscar código, nome ou observações"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onPressEnter={() => {
              setPage(1);
              setSearch(searchInput.trim());
            }}
            style={{ width: 240 }}
            allowClear
          />
          <Select
            placeholder="Produto fabricado"
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

      <Card
        size="small"
        title={editing ? "Editar receita" : "Nova receita"}
        extra={
          editing || formProduto || formNotes || formLines.some((l) => l.insumo) ? (
            <Button type="link" onClick={resetForm}>
              Cancelar
            </Button>
          ) : null
        }
      >
        <Form layout="vertical" onFinish={() => void submitForm()}>
          {!editing ? (
            <Form.Item label="Produto fabricado *" required>
              <Select
                placeholder="Selecione…"
                value={formProduto || undefined}
                onChange={(v) => setFormProduto(v ?? "")}
                options={productsMfg.map((p) => ({
                  value: String(p.id),
                  label: `${p.sku} — ${p.nome}`,
                }))}
                showSearch
                optionFilterProp="label"
                style={{ maxWidth: 400 }}
              />
            </Form.Item>
          ) : (
            <Typography.Paragraph>
              Produto:{" "}
              <strong>
                {productById(editing.produto)?.sku} — {productById(editing.produto)?.nome}
              </strong>
            </Typography.Paragraph>
          )}
          {finishedProdutoId ? (
            <div
              style={{
                marginBottom: 16,
                padding: 12,
                borderRadius: token.borderRadiusLG,
                background: token.colorFillAlter,
                border: `1px solid ${token.colorBorderSecondary}`,
              }}
            >
              <Typography.Text strong>Custo estimado (insumos da receita)</Typography.Text>
              <Typography.Paragraph type="secondary" style={{ marginBottom: 10, marginTop: 4, fontSize: 12 }}>
              </Typography.Paragraph>
              <Space size={24} wrap align="start">
                <div>
                 

                  {!costPreview.hasValidLines ? (
                    <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                      Preencha insumo e quantidade para somar.
                    </Typography.Text>
                  ) : null}
                </div>
                {costPreview.impliedUnitCost != null && costPreview.impliedOutputUnit ? (
                  <div>
                    <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                      Custo unitário implícito
                    </Typography.Text>
                    <Typography.Title level={4} style={{ margin: "4px 0 0" }}>
                      {formatarBRL(costPreview.impliedUnitCost)}
                    </Typography.Title>
                    <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                      por {unitLabel(costPreview.impliedOutputUnit)} fabricado(a) 
                    </Typography.Text>
                  </div>
                ) : null}
                {finishedProdutoForCost ? (
                  <div>
                    <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                      Custo unitário na ficha do produto
                    </Typography.Text>
                    <Typography.Title level={5} style={{ margin: "4px 0 0" }}>
                      {formatarBRL(Number(String(finishedProdutoForCost.custo_unitario).replace(",", ".")) || 0)}
                    </Typography.Title>
                    <Typography.Text type="secondary" style={{ fontSize: 11 }}>
                      Origem:{" "}
                      {finishedProdutoForCost.origem_custo === "receita" ? "Receita" : "Cadastro"}
                    </Typography.Text>
                  </div>
                ) : null}
              </Space>
            </div>
          ) : null}
          <Form.Item label="Observações">
            <Input.TextArea
              value={formNotes}
              onChange={(e) => setFormNotes(e.target.value)}
              rows={2}
            />
          </Form.Item>
          <Space direction="vertical" style={{ width: "100%" }} size="middle">
            <Space>
              <Typography.Text type="secondary">Insumos (por unidade produzida)</Typography.Text>
              <Button type="dashed" icon={<PlusOutlined />} onClick={addLine}>
                Linha
              </Button>
            </Space>
            {formLines.map((row, idx) => (
              <Space key={idx} wrap style={{ width: "100%" }} align="start">
                <Form.Item label="Insumo" style={{ minWidth: 240, marginBottom: 0 }}>
                  <Select
                    placeholder="Selecione…"
                    value={row.insumo || undefined}
                    onChange={(v) => {
                      const id = v ?? "";
                      const p = productsAll.find((x) => String(x.id) === id);
                      updateLine(idx, {
                        insumo: id,
                        quantidade_por_unidade_unidade: p ? coerceProductUnitCode(p.unidade) : "",
                      });
                    }}
                    showSearch
                    optionFilterProp="label"
                    options={productsAll.map((p) => ({
                      value: String(p.id),
                      label: `${p.sku} — ${p.nome}`,
                    }))}
                    style={{ width: 280 }}
                  />
                </Form.Item>
                <Form.Item label="Qtd / un. fab." style={{ width: 120, marginBottom: 0 }}>
                  <Input
                    inputMode="decimal"
                    value={row.quantidade_por_unidade}
                    onChange={(e) => updateLine(idx, { quantidade_por_unidade: e.target.value })}
                  />
                </Form.Item>
                <Form.Item label="Unidade" style={{ width: 200, marginBottom: 0 }}>
                  <Select<ProductUnitCode>
                    disabled={!row.insumo}
                    value={row.quantidade_por_unidade_unidade || undefined}
                    placeholder="Insumo…"
                    onChange={(v) => updateLine(idx, { quantidade_por_unidade_unidade: v })}
                    options={unitOptionsForComponent(row.insumo)}
                  />
                </Form.Item>
                <Tooltip title="Remover linha">
                  <Button
                    danger
                    type="text"
                    icon={<DeleteOutlined />}
                    aria-label="Remover linha"
                    onClick={() => removeLine(idx)}
                    disabled={formLines.length <= 1}
                    style={{ marginTop: 30 }}
                  />
                </Tooltip>
              </Space>
            ))}
          </Space>
          <Button type="primary" htmlType="submit" loading={saving} style={{ marginTop: 16 }}>
            {editing ? "Salvar" : "Criar"}
          </Button>
        </Form>
      </Card>

      {err ? <Alert type="error" message={err} showIcon /> : null}

      <Spin spinning={loading}>
        <Table<Receita> rowKey="id" columns={columns} dataSource={list} pagination={false} />
        <BarraPaginacao page={page} totalCount={count} pageSize={PAGE_SIZE} onPageChange={setPage} />
      </Spin>
    </Space>
  );
}
