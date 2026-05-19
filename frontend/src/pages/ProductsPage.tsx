import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Alert,
  Button,
  Card,
  Checkbox,
  Form,
  Input,
  Popconfirm,
  Select,
  Space,
  Spin,
  Table,
  Tooltip,
  Typography,
} from "antd";
import { DeleteOutlined, EditOutlined } from "@ant-design/icons";
import { PaginationBar } from "../components/PaginationBar";
import { formatQuantityDisplay } from "../utils/quantityDisplay";
import {
  createProduct,
  deleteProduct,
  fetchAllCategories,
  fetchAllSuppliers,
  listProducts,
  updateProduct,
} from "../api/catalog";
import {
  coerceProductUnitCode,
  DEFAULT_PRODUCT_UNIT,
  PRODUCT_UNIT_OPTIONS,
} from "../constants/units";
import type {
  Category,
  Product,
  ProductCostOrigin,
  ProductType,
  ProductUnitCode,
  Supplier,
} from "../types/catalog";
import type { ColumnsType } from "antd/es/table";

const PAGE_SIZE = 20;

const moneyStr = (v: string | undefined) => (v == null || v === "" ? "0" : v);

function parsePositiveDecimal(raw: string | undefined): number | null {
  const t = (raw ?? "").trim().replace(",", ".");
  if (t === "") return null;
  const n = Number(t);
  if (!Number.isFinite(n)) return null;
  return n;
}

const costOriginLabel = (o: ProductCostOrigin) =>
  o === "bom" ? "Receita (BOM)" : "Aquisição";

const emptyForm = {
  sku: "",
  name: "",
  description: "",
  category: "" as number | "",
  supplier: "" as number | "" | null,
  product_type: "purchased" as ProductType,
  unit: DEFAULT_PRODUCT_UNIT,
  sale_price: "0",
  purchase_unit_cost: "0",
  min_stock: "0",
  unit_cost_display: "",
  is_active: true,
};

export function ProductsPage() {
  const [list, setList] = useState<Product[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [filterCategory, setFilterCategory] = useState<string>("");
  const [filterType, setFilterType] = useState<string>("");
  const [filterActive, setFilterActive] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [editing, setEditing] = useState<Product | null>(null);
  const [saving, setSaving] = useState(false);
  const [categories, setCategories] = useState<Category[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);

  useEffect(() => {
    void (async () => {
      try {
        const [cats, sups] = await Promise.all([fetchAllCategories(), fetchAllSuppliers()]);
        setCategories(cats);
        setSuppliers(sups);
      } catch {
        /* lista de produtos ainda pode funcionar parcialmente */
      }
    })();
  }, []);

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const data = await listProducts({
        page,
        search: search || undefined,
        category: filterCategory || undefined,
        product_type: filterType || undefined,
        is_active: filterActive === "" ? undefined : filterActive === "true",
        ordering: "name",
      });
      setList(data.results);
      setCount(data.count);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao listar");
    } finally {
      setLoading(false);
    }
  }, [page, search, filterCategory, filterType, filterActive]);

  useEffect(() => {
    void load();
  }, [load]);

  const buildPayload = (): Record<string, unknown> => {
    const categoryId = form.category === "" ? null : Number(form.category);
    if (categoryId === null || Number.isNaN(categoryId)) {
      throw new Error("Selecione uma categoria");
    }
    const payload: Record<string, unknown> = {
      sku: form.sku.trim(),
      name: form.name.trim(),
      description: form.description.trim(),
      category: categoryId,
      product_type: form.product_type,
      unit: form.unit,
      sale_price: moneyStr(form.sale_price),
      min_stock: form.min_stock,
      is_active: form.is_active,
    };
    if (form.product_type === "purchased") {
      payload.purchase_unit_cost = moneyStr(form.purchase_unit_cost);
    } else {
      payload.purchase_unit_cost = "0";
    }
    if (form.supplier === "" || form.supplier === null) {
      payload.supplier = null;
    } else {
      payload.supplier = Number(form.supplier);
    }
    return payload;
  };

  const submitForm = async () => {
    setSaving(true);
    setErr(null);
    try {
      const sp = parsePositiveDecimal(form.sale_price);
      if (sp === null || sp <= 0) {
        setErr("Informe o preço de venda maior que zero.");
        return;
      }
      if (form.product_type === "purchased") {
        const pc = parsePositiveDecimal(form.purchase_unit_cost);
        if (pc === null || pc <= 0) {
          setErr("Informe o custo de aquisição maior que zero.");
          return;
        }
      }
      const payload = buildPayload();
      if (editing) {
        await updateProduct(editing.id, payload);
      } else {
        await createProduct(payload);
      }
      setForm(emptyForm);
      setEditing(null);
      await load();
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Erro ao salvar");
    } finally {
      setSaving(false);
    }
  };

  const startEdit = (p: Product) => {
    setEditing(p);
    setForm({
      sku: p.sku,
      name: p.name,
      description: p.description,
      category: p.category,
      supplier: p.supplier ?? "",
      product_type: p.product_type,
      unit: coerceProductUnitCode(p.unit),
      sale_price: moneyStr(p.sale_price ?? "0"),
      purchase_unit_cost: moneyStr(p.purchase_unit_cost ?? "0"),
      unit_cost_display: moneyStr(p.unit_cost ?? "0"),
      min_stock: p.min_stock,
      is_active: p.is_active,
    });
  };

  const cancelForm = () => {
    setEditing(null);
    setForm(emptyForm);
  };

  const handleDelete = async (p: Product) => {
    setErr(null);
    try {
      await deleteProduct(p.id);
      if (editing?.id === p.id) cancelForm();
      await load();
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Erro ao excluir");
    }
  };

  const columns: ColumnsType<Product> = useMemo(
    () => [
      { title: "SKU", dataIndex: "sku", key: "sku" },
      { title: "Nome", dataIndex: "name", key: "name" },
      { title: "Categoria", dataIndex: "category_name", key: "category_name" },
      {
        title: "Tipo",
        dataIndex: "product_type",
        key: "product_type",
        render: (t: ProductType) => (t === "purchased" ? "Comprado" : "Produzido"),
      },
      { title: "Unid.", dataIndex: "unit", key: "unit", width: 56 },
      {
        title: "Venda R$",
        dataIndex: "sale_price",
        key: "sale_price",
        width: 88,
        render: (v: string) => moneyStr(v),
      },
      {
        title: "Custo R$",
        dataIndex: "unit_cost",
        key: "unit_cost",
        width: 88,
        render: (v: string) => moneyStr(v),
      },
      {
        title: "Origem custo",
        dataIndex: "cost_origin",
        key: "cost_origin",
        width: 110,
        render: (o: ProductCostOrigin | undefined) => costOriginLabel(o ?? "purchase"),
      },
      {
        title: "Mín.",
        dataIndex: "min_stock",
        key: "min_stock",
        width: 80,
        render: (v: string) => formatQuantityDisplay(v),
      },
      {
        title: "Ativo",
        dataIndex: "is_active",
        key: "is_active",
        width: 80,
        render: (v: boolean) => (v ? "Sim" : "Não"),
      },
      {
        title: "Ações",
        key: "actions",
        width: 96,
        render: (_, p) => (
          <Space size={4}>
            <Tooltip title="Editar">
              <Button
                type="text"
                icon={<EditOutlined />}
                aria-label="Editar"
                onClick={() => startEdit(p)}
              />
            </Tooltip>
            <Tooltip title="Excluir">
              <Popconfirm
                title={`Excluir produto "${p.name}" (${p.sku})?`}
                okText="Excluir"
                cancelText="Cancelar"
                okButtonProps={{ danger: true }}
                onConfirm={() => void handleDelete(p)}
              >
                <Button type="text" danger icon={<DeleteOutlined />} aria-label="Excluir" />
              </Popconfirm>
            </Tooltip>
          </Space>
        ),
      },
    ],
    [],
  );

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Typography.Title level={3} style={{ margin: 0 }}>
        Produtos
      </Typography.Title>

      <Card size="small" title="Filtros">
        <Space wrap>
          <Input
            placeholder="Buscar SKU ou nome"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onPressEnter={() => {
              setPage(1);
              setSearch(searchInput.trim());
            }}
            style={{ width: 200 }}
            allowClear
          />
          <Select
            placeholder="Categoria"
            value={filterCategory || undefined}
            onChange={(v) => {
              setFilterCategory(v ?? "");
              setPage(1);
            }}
            allowClear
            style={{ width: 200 }}
            options={categories.map((c) => ({ value: String(c.id), label: c.name }))}
          />
          <Select
            placeholder="Tipo"
            value={filterType || undefined}
            onChange={(v) => {
              setFilterType(v ?? "");
              setPage(1);
            }}
            allowClear
            style={{ width: 180 }}
            options={[
              { value: "purchased", label: "Comprado" },
              { value: "manufactured", label: "Produzido" },
            ]}
          />
          <Select
            placeholder="Ativo?"
            value={filterActive || undefined}
            onChange={(v) => {
              setFilterActive(v ?? "");
              setPage(1);
            }}
            allowClear
            style={{ width: 120 }}
            options={[
              { value: "true", label: "Sim" },
              { value: "false", label: "Não" },
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

      <Card
        size="small"
        title={editing ? "Editar produto" : "Novo produto"}
        extra={
          editing ? (
            <Button type="link" onClick={cancelForm}>
              Cancelar
            </Button>
          ) : null
        }
      >
        <Form layout="vertical" onFinish={() => void submitForm()}>
          <Space wrap size="middle" style={{ width: "100%" }}>
            <Form.Item label="SKU *" required style={{ minWidth: 120, marginBottom: 0 }}>
              <Input
                value={form.sku}
                onChange={(e) => setForm((f) => ({ ...f, sku: e.target.value }))}
                disabled={!!editing}
              />
            </Form.Item>
            <Form.Item label="Nome *" required style={{ minWidth: 200, marginBottom: 0 }}>
              <Input
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              />
            </Form.Item>
            <Form.Item label="Categoria *" required style={{ minWidth: 200, marginBottom: 0 }}>
              <Select
                placeholder="Selecione…"
                value={form.category === "" ? undefined : String(form.category)}
                onChange={(v) =>
                  setForm((f) => ({
                    ...f,
                    category: v ? Number(v) : "",
                  }))
                }
                options={categories.map((c) => ({ value: String(c.id), label: c.name }))}
                style={{ width: "100%" }}
              />
            </Form.Item>
            <Form.Item label="Fornecedor (opc.)" style={{ minWidth: 200, marginBottom: 0 }}>
              <Select
                allowClear
                placeholder="—"
                value={
                  form.supplier === "" || form.supplier === null
                    ? undefined
                    : String(form.supplier)
                }
                onChange={(v) =>
                  setForm((f) => ({
                    ...f,
                    supplier: v ? Number(v) : "",
                  }))
                }
                options={suppliers.map((s) => ({ value: String(s.id), label: s.name }))}
                style={{ width: "100%" }}
              />
            </Form.Item>
            <Form.Item label="Tipo *" style={{ minWidth: 220, marginBottom: 0 }}>
              <Select
                value={form.product_type}
                onChange={(v) =>
                  setForm((f) => ({
                    ...f,
                    product_type: v as ProductType,
                    purchase_unit_cost: v === "manufactured" ? "0" : f.purchase_unit_cost,
                  }))
                }
                options={[
                  { value: "purchased", label: "Comprado" },
                  { value: "manufactured", label: "Produzido manualmente" },
                ]}
              />
            </Form.Item>
            <Form.Item label="Unidade *" required style={{ minWidth: 200, marginBottom: 0 }}>
              <Select<ProductUnitCode>
                value={form.unit}
                onChange={(v) => setForm((f) => ({ ...f, unit: v }))}
                options={PRODUCT_UNIT_OPTIONS}
                placeholder="Selecione…"
              />
            </Form.Item>
            <Form.Item label="Preço de venda (R$) *" required style={{ minWidth: 140, marginBottom: 0 }}>
              <Input
                inputMode="decimal"
                value={form.sale_price}
                onChange={(e) => setForm((f) => ({ ...f, sale_price: e.target.value }))}
                placeholder="0,00"
              />
            </Form.Item>
            {form.product_type === "purchased" ? (
              <Form.Item
                label="Custo de aquisição (R$ / unid.) *"
                required
                style={{ minWidth: 200, marginBottom: 0 }}
              >
                <Input
                  inputMode="decimal"
                  value={form.purchase_unit_cost}
                  onChange={(e) => setForm((f) => ({ ...f, purchase_unit_cost: e.target.value }))}
                  placeholder="0,00"
                />
              </Form.Item>
            ) : (
              <Form.Item label="Custo unitário (BOM)" style={{ minWidth: 160, marginBottom: 0 }}>
                <Input value={form.unit_cost_display || "0"} disabled />
              </Form.Item>
            )}
            <Form.Item label="Estoque mínimo" style={{ minWidth: 120, marginBottom: 0 }}>
              <Input
                value={form.min_stock}
                onChange={(e) => setForm((f) => ({ ...f, min_stock: e.target.value }))}
              />
            </Form.Item>
          </Space>
          {form.product_type === "manufactured" ? (
            <Typography.Paragraph type="secondary" style={{ marginBottom: 8 }}>
              Produto fabricado: o custo unitário é calculado pela soma (quantidade do insumo × custo
              unitário do insumo) na receita. Cadastre a receita em Estoque → Receitas (BOM).
            </Typography.Paragraph>
          ) : null}
          <Form.Item label="Descrição">
            <Input.TextArea
              value={form.description}
              onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              rows={2}
            />
          </Form.Item>
          <Checkbox
            checked={form.is_active}
            onChange={(e) => setForm((f) => ({ ...f, is_active: e.target.checked }))}
          >
            Ativo
          </Checkbox>
          <div style={{ marginTop: 12 }}>
            <Button type="primary" htmlType="submit" loading={saving}>
              Salvar
            </Button>
          </div>
        </Form>
      </Card>

      {err ? <Alert type="error" message={err} showIcon /> : null}

      <Spin spinning={loading}>
        <Table<Product> rowKey="id" columns={columns} dataSource={list} pagination={false} />
        <PaginationBar page={page} totalCount={count} pageSize={PAGE_SIZE} onPageChange={setPage} />
      </Spin>
    </Space>
  );
}
