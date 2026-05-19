import { useCallback, useEffect, useMemo, useState } from "react";
import {
  coerceProductUnitCode,
  compatibleUnitsForProduct,
  PRODUCT_UNIT_OPTIONS,
} from "../../constants/units";
import type { ProductUnitCode } from "../../constants/units";
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
import { PaginationBar } from "../../components/PaginationBar";
import { fetchAllProducts } from "../../api/catalog";
import {
  createRecipe,
  deleteRecipe,
  getRecipe,
  listRecipes,
  updateRecipe,
} from "../../api/stock";
import type { Product } from "../../types/catalog";
import type { Recipe, RecipeLine } from "../../types/stock";
import type { ColumnsType } from "antd/es/table";
import {
  estimateProductionCostPreview,
  formatBRL,
  unitLabel,
} from "../../utils/productionCostPreview";

const PAGE_SIZE = 20;

type LineForm = {
  component: string;
  quantity_per_unit: string;
  quantity_per_unit_unit: ProductUnitCode | "";
};

const emptyLine = (): LineForm => ({
  component: "",
  quantity_per_unit: "",
  quantity_per_unit_unit: "",
});

export function RecipesPage() {
  const { token } = theme.useToken();
  const [list, setList] = useState<Recipe[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [filterProduct, setFilterProduct] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const [productsMfg, setProductsMfg] = useState<Product[]>([]);
  const [productsAll, setProductsAll] = useState<Product[]>([]);

  const [editing, setEditing] = useState<Recipe | null>(null);
  const [formProduct, setFormProduct] = useState("");
  const [formNotes, setFormNotes] = useState("");
  const [formLines, setFormLines] = useState<LineForm[]>([emptyLine()]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    void (async () => {
      try {
        const [mfg, all] = await Promise.all([
          fetchAllProducts({ product_type: "manufactured", is_active: true }),
          fetchAllProducts({ is_active: true }),
        ]);
        setProductsMfg(mfg);
        setProductsAll(all);
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
      const codes = compatibleUnitsForProduct(coerceProductUnitCode(p.unit));
      return PRODUCT_UNIT_OPTIONS.filter((o) => codes.includes(o.value));
    },
    [productsAll],
  );

  const finishedProductId = editing ? String(editing.product) : formProduct;
  const finishedProductForCost = finishedProductId
    ? productsMfg.find((p) => String(p.id) === finishedProductId)
    : undefined;

  const linesAsProductionPreview = useMemo(
    () =>
      formLines.map((row) => ({
        component: row.component,
        quantity_consumed: row.quantity_per_unit,
        quantity_consumed_unit: row.quantity_per_unit_unit,
      })),
    [formLines],
  );

  const costPreview = useMemo(() => {
    if (!finishedProductForCost) {
      return estimateProductionCostPreview({
        producedProduct: undefined,
        qtyProducedStr: "",
        qtyProducedUnit: "UN",
        lines: linesAsProductionPreview,
        componentsCatalog: productsAll,
      });
    }
    const cat = coerceProductUnitCode(finishedProductForCost.unit);
    return estimateProductionCostPreview({
      producedProduct: finishedProductForCost,
      qtyProducedStr: "1",
      qtyProducedUnit: cat,
      lines: linesAsProductionPreview,
      componentsCatalog: productsAll,
    });
  }, [finishedProductForCost, linesAsProductionPreview, productsAll]);

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const data = await listRecipes({
        page,
        search: search || undefined,
        product: filterProduct || undefined,
        ordering: "-updated_at",
      });
      setList(data.results);
      setCount(data.count);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao listar");
    } finally {
      setLoading(false);
    }
  }, [page, search, filterProduct]);

  useEffect(() => {
    void load();
  }, [load]);

  const resetForm = () => {
    setEditing(null);
    setFormProduct("");
    setFormNotes("");
    setFormLines([emptyLine()]);
  };

  const linesFromRecipe = (lines: RecipeLine[]): LineForm[] =>
    lines.length
      ? lines.map((l) => {
          const p = productsAll.find((x) => x.id === l.component);
          return {
            component: String(l.component),
            quantity_per_unit: l.quantity_per_unit,
            quantity_per_unit_unit: p ? coerceProductUnitCode(p.unit) : "",
          };
        })
      : [emptyLine()];

  const startEdit = async (r: Recipe) => {
    setErr(null);
    try {
      const full = await getRecipe(r.id);
      setEditing(full);
      setFormProduct(String(full.product));
      setFormNotes(full.notes);
      setFormLines(linesFromRecipe(full.lines));
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao carregar receita");
    }
  };

  const buildLinesPayload = (): Array<{
    component: number;
    quantity_per_unit: string;
    quantity_per_unit_unit?: string;
  }> => {
    const out: Array<{
      component: number;
      quantity_per_unit: string;
      quantity_per_unit_unit?: string;
    }> = [];
    for (const row of formLines) {
      if (!row.component.trim() || !row.quantity_per_unit.trim()) continue;
      const line: {
        component: number;
        quantity_per_unit: string;
        quantity_per_unit_unit?: string;
      } = {
        component: Number(row.component),
        quantity_per_unit: row.quantity_per_unit.trim(),
      };
      if (row.quantity_per_unit_unit) {
        line.quantity_per_unit_unit = row.quantity_per_unit_unit;
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
        await updateRecipe(editing.id, {
          notes: formNotes.trim(),
          lines: linesPayload,
        });
      } else {
        if (!formProduct) {
          setErr("Selecione o produto fabricado.");
          setSaving(false);
          return;
        }
        await createRecipe({
          product: Number(formProduct),
          notes: formNotes.trim() || undefined,
          lines: linesPayload,
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

  const handleDelete = async (r: Recipe) => {
    setErr(null);
    try {
      await deleteRecipe(r.id);
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

  const columns: ColumnsType<Recipe> = useMemo(
    () => [
      {
        title: "Produto",
        key: "product",
        render: (_, r) => {
          const p = productById(r.product);
          return p ? `${p.sku} — ${p.name}` : `#${r.product}`;
        },
      },
      { title: "Linhas", key: "lines", render: (_, r) => r.lines?.length ?? 0 },
      {
        title: "Atualizado",
        dataIndex: "updated_at",
        key: "updated_at",
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
      <Typography.Paragraph type="secondary">Insumos por 1 unidade do produto fabricado.</Typography.Paragraph>

      <Card size="small" title="Filtros">
        <Space wrap>
          <Input
            placeholder="Buscar SKU, nome ou observações"
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
            value={filterProduct || undefined}
            onChange={(v) => {
              setFilterProduct(v ?? "");
              setPage(1);
            }}
            allowClear
            showSearch
            optionFilterProp="label"
            style={{ width: 280 }}
            options={productsMfg.map((p) => ({
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

      <Card
        size="small"
        title={editing ? "Editar receita" : "Nova receita"}
        extra={
          editing || formProduct || formNotes || formLines.some((l) => l.component) ? (
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
                value={formProduct || undefined}
                onChange={(v) => setFormProduct(v ?? "")}
                options={productsMfg.map((p) => ({
                  value: String(p.id),
                  label: `${p.sku} — ${p.name}`,
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
                {productById(editing.product)?.sku} — {productById(editing.product)?.name}
              </strong>
            </Typography.Paragraph>
          )}
          {finishedProductId ? (
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
                      {formatBRL(costPreview.impliedUnitCost)}
                    </Typography.Title>
                    <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                      por {unitLabel(costPreview.impliedOutputUnit)} fabricado(a) 
                    </Typography.Text>
                  </div>
                ) : null}
                {finishedProductForCost ? (
                  <div>
                    <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                      Custo unitário na ficha do produto
                    </Typography.Text>
                    <Typography.Title level={5} style={{ margin: "4px 0 0" }}>
                      {formatBRL(Number(String(finishedProductForCost.unit_cost).replace(",", ".")) || 0)}
                    </Typography.Title>
                    <Typography.Text type="secondary" style={{ fontSize: 11 }}>
                      Origem:{" "}
                      {finishedProductForCost.cost_origin === "bom" ? "BOM / receita" : "Cadastro"}
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
                    value={row.component || undefined}
                    onChange={(v) => {
                      const id = v ?? "";
                      const p = productsAll.find((x) => String(x.id) === id);
                      updateLine(idx, {
                        component: id,
                        quantity_per_unit_unit: p ? coerceProductUnitCode(p.unit) : "",
                      });
                    }}
                    showSearch
                    optionFilterProp="label"
                    options={productsAll.map((p) => ({
                      value: String(p.id),
                      label: `${p.sku} — ${p.name}`,
                    }))}
                    style={{ width: 280 }}
                  />
                </Form.Item>
                <Form.Item label="Qtd / un. fab." style={{ width: 120, marginBottom: 0 }}>
                  <Input
                    inputMode="decimal"
                    value={row.quantity_per_unit}
                    onChange={(e) => updateLine(idx, { quantity_per_unit: e.target.value })}
                  />
                </Form.Item>
                <Form.Item label="Unidade" style={{ width: 200, marginBottom: 0 }}>
                  <Select<ProductUnitCode>
                    disabled={!row.component}
                    value={row.quantity_per_unit_unit || undefined}
                    placeholder="Insumo…"
                    onChange={(v) => updateLine(idx, { quantity_per_unit_unit: v })}
                    options={unitOptionsForComponent(row.component)}
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
        <Table<Recipe> rowKey="id" columns={columns} dataSource={list} pagination={false} />
        <PaginationBar page={page} totalCount={count} pageSize={PAGE_SIZE} onPageChange={setPage} />
      </Spin>
    </Space>
  );
}
