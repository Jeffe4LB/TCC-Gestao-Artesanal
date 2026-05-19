import { useCallback, useEffect, useMemo, useState } from "react";
import {
  coerceProductUnitCode,
  compatibleUnitsForProduct,
  PRODUCT_UNIT_OPTIONS,
} from "../../constants/units";
import type { ProductUnitCode } from "../../constants/units";
import { Link } from "react-router-dom";
import {
  Alert,
  Button,
  Card,
  Form,
  Input,
  Select,
  Space,
  Spin,
  Table,
  theme,
  Tooltip,
  Typography,
} from "antd";
import { DeleteOutlined, PlusOutlined } from "@ant-design/icons";
import { PaginationBar } from "../../components/PaginationBar";
import { fetchAllProducts } from "../../api/catalog";
import { createProductionRun, getRecipe, listProductionRuns, listRecipes } from "../../api/stock";
import type { Product } from "../../types/catalog";
import type { ProductionRun, Recipe } from "../../types/stock";
import type { ColumnsType } from "antd/es/table";
import { formatQuantityDisplay } from "../../utils/quantityDisplay";
import {
  estimateProductionCostPreview,
  formatBRL,
  unitLabel,
} from "../../utils/productionCostPreview";
import { buildProductionLinesFromRecipe } from "../../utils/recipeProductionPrefill";

const PAGE_SIZE = 20;

type LineForm = { component: string; quantity_consumed: string; quantity_consumed_unit: ProductUnitCode | "" };

const emptyLine = (): LineForm => ({ component: "", quantity_consumed: "", quantity_consumed_unit: "" });

export function ProductionRunsPage() {
  const { token } = theme.useToken();
  const [list, setList] = useState<ProductionRun[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [filterProduct, setFilterProduct] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const [productsMfg, setProductsMfg] = useState<Product[]>([]);
  const [productsAll, setProductsAll] = useState<Product[]>([]);

  const [formProduct, setFormProduct] = useState("");
  const [formQty, setFormQty] = useState("");
  const [formQtyUnit, setFormQtyUnit] = useState<ProductUnitCode>("UN");
  const [formNotes, setFormNotes] = useState("");
  const [formLines, setFormLines] = useState<LineForm[]>([emptyLine()]);
  const [recipeSnapshot, setRecipeSnapshot] = useState<Recipe | null>(null);
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
        /* */
      }
    })();
  }, []);

  useEffect(() => {
    const p = productsMfg.find((x) => String(x.id) === formProduct);
    if (p) {
      // Unidade de cadastro (ex.: ML, G): alinha com custo unitário do produto, que é por 1 unidade de cadastro.
      setFormQtyUnit(coerceProductUnitCode(p.unit));
    }
  }, [formProduct, productsMfg]);

  const producedUnitOptions = useMemo(() => {
    const p = productsMfg.find((x) => String(x.id) === formProduct);
    if (!p) return PRODUCT_UNIT_OPTIONS;
    const codes = compatibleUnitsForProduct(coerceProductUnitCode(p.unit));
    return PRODUCT_UNIT_OPTIONS.filter((o) => codes.includes(o.value));
  }, [formProduct, productsMfg]);

  useEffect(() => {
    setRecipeSnapshot(null);
    if (!formProduct || !productsAll.length) {
      return;
    }
    setFormLines([emptyLine()]);
    let cancelled = false;
    void (async () => {
      try {
        const res = await listRecipes({ product: Number(formProduct), page: 1 });
        if (cancelled) return;
        if (!res.results.length) {
          setRecipeSnapshot(null);
          return;
        }
        const recipe = await getRecipe(res.results[0].id);
        if (!cancelled) setRecipeSnapshot(recipe);
      } catch {
        if (!cancelled) setRecipeSnapshot(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [formProduct, productsAll]);

  useEffect(() => {
    if (!formProduct) {
      setFormLines([emptyLine()]);
      return;
    }
    if (!recipeSnapshot || String(recipeSnapshot.product) !== formProduct) {
      return;
    }
    const finished = productsMfg.find((p) => String(p.id) === formProduct);
    if (!finished) return;
    const map = new Map(productsAll.map((p) => [p.id, p]));
    setFormLines(buildProductionLinesFromRecipe(recipeSnapshot, finished, map, formQty, formQtyUnit));
  }, [recipeSnapshot, formProduct, formQty, formQtyUnit, productsMfg, productsAll]);

  const unitOptionsForComponent = useCallback((componentId: string) => {
    const p = productsAll.find((x) => String(x.id) === componentId);
    if (!p) return PRODUCT_UNIT_OPTIONS;
    const codes = compatibleUnitsForProduct(coerceProductUnitCode(p.unit));
    return PRODUCT_UNIT_OPTIONS.filter((o) => codes.includes(o.value));
  }, [productsAll]);

  const costPreview = useMemo(
    () =>
      estimateProductionCostPreview({
        producedProduct: productsMfg.find((p) => String(p.id) === formProduct),
        qtyProducedStr: formQty,
        qtyProducedUnit: formQtyUnit,
        lines: formLines,
        componentsCatalog: productsAll,
      }),
    [formProduct, formQty, formQtyUnit, formLines, productsMfg, productsAll],
  );

  const finishedProduct = useMemo(
    () => productsMfg.find((p) => String(p.id) === formProduct),
    [formProduct, productsMfg],
  );

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const data = await listProductionRuns({
        page,
        search: search || undefined,
        product: filterProduct || undefined,
        ordering: "-created_at",
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

  const buildLinesPayload = (): Array<{
    component: number;
    quantity_consumed: string;
    quantity_consumed_unit?: string;
  }> => {
    const out: Array<{
      component: number;
      quantity_consumed: string;
      quantity_consumed_unit?: string;
    }> = [];
    for (const row of formLines) {
      if (!row.component.trim() || !row.quantity_consumed.trim()) continue;
      const line: {
        component: number;
        quantity_consumed: string;
        quantity_consumed_unit?: string;
      } = {
        component: Number(row.component),
        quantity_consumed: row.quantity_consumed.trim(),
      };
      if (row.quantity_consumed_unit) {
        line.quantity_consumed_unit = row.quantity_consumed_unit;
      }
      out.push(line);
    }
    return out;
  };

  const resetForm = () => {
    setFormProduct("");
    setFormQty("");
    setFormQtyUnit("UN");
    setFormNotes("");
    setRecipeSnapshot(null);
    setFormLines([emptyLine()]);
  };

  const submitForm = async () => {
    const linesPayload = buildLinesPayload();
    if (!formProduct) {
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
      await createProductionRun({
        product: Number(formProduct),
        quantity_produced: qtyNorm,
        quantity_produced_unit: formQtyUnit,
        lines: linesPayload,
        notes: formNotes.trim() || undefined,
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

  const columns: ColumnsType<ProductionRun> = useMemo(
    () => [
      {
        title: "Data",
        dataIndex: "created_at",
        key: "created_at",
        render: (v: string) => new Date(v).toLocaleString(),
      },
      {
        title: "Produto",
        key: "product",
        render: (_, run) => `${run.product_sku} — ${run.product_name}`,
      },
      {
        title: "Qtd",
        dataIndex: "quantity_produced",
        key: "quantity_produced",
        render: (v: string) => formatQuantityDisplay(v),
      },
      {
        title: "Detalhe",
        key: "detail",
        render: (_, run) => (
          <Link to={`/app/estoque/producao/${run.id}`}>
            <Typography.Link>Ver</Typography.Link>
          </Link>
        ),
      },
    ],
    [],
  );

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Typography.Title level={3} style={{ margin: 0 }}>
        Produção
      </Typography.Title>

      <Card size="small" title="Filtros">
        <Space wrap>
          <Input
            placeholder="Buscar SKU ou observações"
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

      <Card size="small" title="Nova ordem de produção">
        <Form layout="vertical" onFinish={() => void submitForm()}>
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
          <Form.Item label="Quantidade produzida *" required>
            <Space wrap align="start">
              <Input
                inputMode="decimal"
                value={formQty}
                onChange={(e) => setFormQty(e.target.value)}
                placeholder="> 0"
                style={{ width: 160 }}
              />
              <Select<ProductUnitCode>
                style={{ width: 200 }}
                value={formQtyUnit}
                onChange={(v) => setFormQtyUnit(v)}
                options={producedUnitOptions}
              />
            </Space>
          </Form.Item>
          {formProduct ? (
            <div
              style={{
                marginBottom: 16,
                padding: 12,
                borderRadius: token.borderRadiusLG,
                background: token.colorFillAlter,
                border: `1px solid ${token.colorBorderSecondary}`,
              }}
            >
              <Typography.Text strong style={{ display: 'block' }}>
                Custo estimado
              </Typography.Text>
              

              <Space size={24} wrap align="start">
                <div>
                  <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                    Total de insumos
                  </Typography.Text>
                  <Typography.Title level={4} style={{ margin: "4px 0 0" }}>
                    {formatBRL(costPreview.materialsTotal)}
                  </Typography.Title>
                  {!costPreview.hasValidLines ? (
                    <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                      Preencha insumo e quantidade para somar.
                    </Typography.Text>
                  ) : null}
                </div>
                
                {finishedProduct ? (
                  <div>
                    <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                      Custo unitário na ficha do produto
                    </Typography.Text>
                    <Typography.Title level={5} style={{ margin: "4px 0 0" }}>
                      {formatBRL(Number(String(finishedProduct.unit_cost).replace(",", ".")) || 0)}
                    </Typography.Title>
                    <Typography.Text type="secondary" style={{ fontSize: 11 }}>
                      Origem: {finishedProduct.cost_origin === "bom" ? "Receita" : "Cadastro"}
                    </Typography.Text>
                  </div>
                ) : null}
              </Space>
            </div>
          ) : null}
          <Form.Item label="Observações">
            <Input value={formNotes} onChange={(e) => setFormNotes(e.target.value)} />
          </Form.Item>
          <Space direction="vertical" style={{ width: "100%" }} size="middle">
            <Space>
              <Typography.Text type="secondary">Consumo de insumos (totais nesta ordem)</Typography.Text>
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
                      const defaultUnit: ProductUnitCode | "" = p ? coerceProductUnitCode(p.unit) : "";
                      updateLine(idx, {
                        component: id,
                        quantity_consumed_unit: defaultUnit,
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
                <Form.Item label="Qtd consumida" style={{ width: 120, marginBottom: 0 }}>
                  <Input
                    inputMode="decimal"
                    value={row.quantity_consumed}
                    onChange={(e) => updateLine(idx, { quantity_consumed: e.target.value })}
                  />
                </Form.Item>
                <Form.Item label="Unidade" style={{ width: 200, marginBottom: 0 }}>
                  <Select<ProductUnitCode>
                    disabled={!row.component}
                    value={row.quantity_consumed_unit || undefined}
                    placeholder="Insumo…"
                    onChange={(v) => updateLine(idx, { quantity_consumed_unit: v })}
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
          <Space style={{ marginTop: 16 }}>
            <Button type="primary" htmlType="submit" loading={saving}>
              Registrar produção
            </Button>
            <Button onClick={resetForm}>Limpar</Button>
          </Space>
        </Form>
      </Card>

      {err ? <Alert type="error" message={err} showIcon /> : null}

      <Spin spinning={loading}>
        <Table<ProductionRun> rowKey="id" columns={columns} dataSource={list} pagination={false} />
        <PaginationBar page={page} totalCount={count} pageSize={PAGE_SIZE} onPageChange={setPage} />
      </Spin>
    </Space>
  );
}
