import { useCallback, useEffect, useMemo, useState } from "react";
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
  Typography,
} from "antd";
import { PaginationBar } from "../../components/PaginationBar";
import { fetchAllProducts } from "../../api/catalog";
import { createStockMovement, listStockMovements } from "../../api/stock";
import {
  baseUnitForProductUnit,
  coerceProductUnitCode,
  compatibleUnitsForProduct,
  PRODUCT_UNIT_OPTIONS,
} from "../../constants/units";
import type { Product } from "../../types/catalog";
import type { ProductUnitCode } from "../../constants/units";
import type { StockMovementRow } from "../../types/stock";
import type { ColumnsType } from "antd/es/table";
import { formatQuantityWithUnit } from "../../utils/quantityDisplay";

const PAGE_SIZE = 20;

const MOVEMENT_LABEL: Record<string, string> = {
  purchase_in: "Compra",
  adjustment: "Ajuste",
  production_consumption: "Consumo (produção)",
  production_output: "Saída produto acabado",
  receivable_sale: "Venda (conta a receber)",
  receivable_sale_reversal: "Estorno venda (conta a receber)",
};

function formatMovementType(code: string) {
  return MOVEMENT_LABEL[code] ?? code;
}

export function StockMovementsPage() {
  const [list, setList] = useState<StockMovementRow[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [productId, setProductId] = useState<string>("");
  const [movementType, setMovementType] = useState<string>("");
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const [formType, setFormType] = useState<"purchase_in" | "adjustment">("purchase_in");
  const [formProduct, setFormProduct] = useState<string>("");
  const [formUnit, setFormUnit] = useState<ProductUnitCode>("UN");
  const [formQty, setFormQty] = useState("");
  const [formNotes, setFormNotes] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    void fetchAllProducts({ is_active: true }).then(setProducts).catch(() => {});
  }, []);

  useEffect(() => {
    const p = products.find((x) => String(x.id) === formProduct);
    if (p) {
      const u = coerceProductUnitCode(p.unit);
      setFormUnit(baseUnitForProductUnit(u));
    }
  }, [formProduct, products]);

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const data = await listStockMovements({
        page,
        search: search || undefined,
        product: productId || undefined,
        movement_type: movementType || undefined,
        ordering: "-created_at",
      });
      setList(data.results);
      setCount(data.count);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao listar");
    } finally {
      setLoading(false);
    }
  }, [page, search, productId, movementType]);

  useEffect(() => {
    void load();
  }, [load]);

  const submitMovement = async () => {
    if (!formProduct) {
      setErr("Selecione o produto.");
      return;
    }
    const qtyNum = Number(String(formQty).trim().replace(",", "."));
    if (!Number.isFinite(qtyNum)) {
      setErr("Quantidade inválida.");
      return;
    }
    if (formType === "purchase_in" && qtyNum <= 0) {
      setErr("Na compra, a quantidade deve ser maior que zero.");
      return;
    }
    if (formType === "adjustment" && qtyNum === 0) {
      setErr("Ajuste não pode ser zero (use valor negativo para baixa).");
      return;
    }
    setSaving(true);
    setErr(null);
    try {
      await createStockMovement({
        movement_type: formType,
        product: Number(formProduct),
        quantity: formQty.trim(),
        unit: formUnit,
        notes: formNotes.trim() || undefined,
      });
      setFormQty("");
      setFormNotes("");
      await load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao lançar");
    } finally {
      setSaving(false);
    }
  };

  const unitOptionsForForm = useMemo(() => {
    const p = products.find((x) => String(x.id) === formProduct);
    if (!p) return PRODUCT_UNIT_OPTIONS;
    const codes = compatibleUnitsForProduct(coerceProductUnitCode(p.unit));
    return PRODUCT_UNIT_OPTIONS.filter((o) => codes.includes(o.value));
  }, [formProduct, products]);

  const columns: ColumnsType<StockMovementRow> = useMemo(
    () => [
      {
        title: "Data",
        dataIndex: "created_at",
        key: "created_at",
        render: (v: string) => new Date(v).toLocaleString(),
      },
      { title: "SKU", dataIndex: "product_sku", key: "product_sku" },
      {
        title: "Δ (base)",
        key: "qd",
        render: (_: unknown, r: StockMovementRow) =>
          formatQuantityWithUnit(r.quantity_delta, r.base_unit),
      },
      {
        title: "Informado",
        key: "qin",
        render: (_: unknown, r: StockMovementRow) =>
          r.quantity_input != null && r.unit_input
            ? formatQuantityWithUnit(r.quantity_input, r.unit_input)
            : "—",
      },
      {
        title: "Tipo",
        dataIndex: "movement_type",
        key: "movement_type",
        render: (c: string) => formatMovementType(c),
      },
      { title: "Obs.", dataIndex: "notes", key: "notes", render: (v) => v || "—" },
    ],
    [],
  );

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Typography.Title level={3} style={{ margin: 0 }}>
        Movimentos
      </Typography.Title>
      <Typography.Paragraph type="secondary">
        Compra e ajuste manual. O saldo é sempre na unidade base (KG, L ou UN). Informe a unidade da
        quantidade (ex.: saída de 50 G com produto em KG). Ajuste pode ser negativo (respeitando
        saldo).
      </Typography.Paragraph>

      <Card size="small" title="Novo lançamento">
        <Form layout="vertical" onFinish={() => void submitMovement()}>
          <Space wrap size="middle" style={{ width: "100%" }}>
            <Form.Item label="Tipo" style={{ minWidth: 200, marginBottom: 0 }}>
              <Select
                value={formType}
                onChange={(v) => setFormType(v as "purchase_in" | "adjustment")}
                options={[
                  { value: "purchase_in", label: "Entrada (compra)" },
                  { value: "adjustment", label: "Ajuste manual" },
                ]}
              />
            </Form.Item>
            <Form.Item label="Produto *" required style={{ minWidth: 260, marginBottom: 0, flex: 1 }}>
              <Select
                placeholder="Selecione…"
                value={formProduct || undefined}
                onChange={(v) => setFormProduct(v ?? "")}
                showSearch
                optionFilterProp="label"
                options={products.map((p) => ({
                  value: String(p.id),
                  label: `${p.sku} — ${p.name}`,
                }))}
                style={{ width: "100%" }}
              />
            </Form.Item>
            <Form.Item label="Quantidade *" required style={{ minWidth: 140, marginBottom: 0 }}>
              <Input
                inputMode="decimal"
                value={formQty}
                onChange={(e) => setFormQty(e.target.value)}
                placeholder={formType === "purchase_in" ? "> 0" : "ex.: 10 ou -2"}
              />
            </Form.Item>
            <Form.Item label="Unidade *" style={{ minWidth: 140, marginBottom: 0 }}>
              <Select<ProductUnitCode>
                value={formUnit}
                onChange={(v) => setFormUnit(v)}
                options={unitOptionsForForm}
              />
            </Form.Item>
            <Form.Item label="Observações" style={{ minWidth: 200, marginBottom: 0 }}>
              <Input value={formNotes} onChange={(e) => setFormNotes(e.target.value)} />
            </Form.Item>
          </Space>
          <Button type="primary" htmlType="submit" loading={saving} style={{ marginTop: 8 }}>
            Registrar
          </Button>
        </Form>
      </Card>

      <Card size="small" title="Listagem — filtros">
        <Space wrap>
          <Input
            placeholder="Buscar SKU ou observação"
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
            value={productId || undefined}
            onChange={(v) => {
              setProductId(v ?? "");
              setPage(1);
            }}
            allowClear
            showSearch
            optionFilterProp="label"
            style={{ width: 280 }}
            options={products.map((p) => ({
              value: String(p.id),
              label: `${p.sku} — ${p.name}`,
            }))}
          />
          <Select
            placeholder="Tipo"
            value={movementType || undefined}
            onChange={(v) => {
              setMovementType(v ?? "");
              setPage(1);
            }}
            allowClear
            style={{ width: 220 }}
            options={[
              { value: "purchase_in", label: "Compra" },
              { value: "adjustment", label: "Ajuste" },
              { value: "production_consumption", label: "Consumo (produção)" },
              { value: "production_output", label: "Saída produto acabado" },
              { value: "receivable_sale", label: "Venda (conta a receber)" },
              { value: "receivable_sale_reversal", label: "Estorno venda (conta a receber)" },
            ]}
          />
          <Button
            type="primary"
            onClick={() => {
              setPage(1);
              setSearch(searchInput.trim());
            }}
          >
            Filtrar
          </Button>
        </Space>
      </Card>

      {err ? <Alert type="error" message={err} showIcon /> : null}

      <Spin spinning={loading}>
        <Table<StockMovementRow> rowKey="id" columns={columns} dataSource={list} pagination={false} />
        <PaginationBar page={page} totalCount={count} pageSize={PAGE_SIZE} onPageChange={setPage} />
      </Spin>
    </Space>
  );
}
