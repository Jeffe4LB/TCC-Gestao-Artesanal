import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Alert,
  Button,
  Card,
  DatePicker,
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
import { DeleteOutlined, EditOutlined, MinusCircleOutlined, PlusOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import { PaginationBar } from "../../components/PaginationBar";
import { fetchAllCustomers, fetchAllProducts } from "../../api/catalog";
import {
  createAccountReceivable,
  deleteAccountReceivable,
  listAccountsReceivable,
  updateAccountReceivable,
} from "../../api/finance";
import {
  coerceProductUnitCode,
  compatibleUnitsForProduct,
  DEFAULT_PRODUCT_UNIT,
  PRODUCT_UNIT_OPTIONS,
} from "../../constants/units";
import type { ProductUnitCode } from "../../constants/units";
import type { Customer, Product } from "../../types/catalog";
import type { AccountReceivable, AccountReceivableLine, ReceivableStatus } from "../../types/finance";
import type { ColumnsType } from "antd/es/table";

const PAGE_SIZE = 20;

const STATUS_LABEL: Record<ReceivableStatus, string> = {
  open: "Em aberto",
  paid: "Recebido",
  cancelled: "Cancelado",
};

function todayLocal(): string {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

type LineForm = {
  product: string;
  quantity: string;
  unit: ProductUnitCode;
  unit_price: string;
  discount: string;
};

const emptyLine = (): LineForm => ({
  product: "",
  quantity: "1",
  unit: DEFAULT_PRODUCT_UNIT,
  unit_price: "0",
  discount: "0",
});

const emptyForm = {
  customer: "",
  description: "",
  issue_date: todayLocal(),
  due_date: "",
  status: "open" as ReceivableStatus,
  received_at: "",
  notes: "",
  lines: [emptyLine()],
};

function lineMoney(q: string, price: string, disc: string): number {
  const a = Number(q) || 0;
  const b = Number(price) || 0;
  const d = Number(disc) || 0;
  return Math.round((a * b - d) * 100) / 100;
}

function parseDecimal(raw: string | undefined): number | null {
  const t = (raw ?? "").trim().replace(",", ".");
  if (t === "") return null;
  const n = Number(t);
  if (!Number.isFinite(n)) return null;
  return n;
}

function mapApiLineToForm(l: AccountReceivableLine): LineForm {
  const u = coerceProductUnitCode(l.unit);
  return {
    product: l.product != null ? String(l.product) : "",
    quantity: String(l.quantity),
    unit: u,
    unit_price: l.unit_price,
    discount: l.discount ?? "0",
  };
}

export function AccountsReceivablePage() {
  const [list, setList] = useState<AccountReceivable[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [filterStatus, setFilterStatus] = useState<string>("");
  const [filterCustomer, setFilterCustomer] = useState<string>("");
  const [dueFrom, setDueFrom] = useState("");
  const [dueTo, setDueTo] = useState("");
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [form, setForm] = useState(emptyForm);
  const [editing, setEditing] = useState<AccountReceivable | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    void fetchAllCustomers().then(setCustomers).catch(() => {});
    void fetchAllProducts({}).then(setProducts).catch(() => {});
  }, []);

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const data = await listAccountsReceivable({
        page,
        search: search || undefined,
        status: filterStatus || undefined,
        customer: filterCustomer || undefined,
        due_from: dueFrom || undefined,
        due_to: dueTo || undefined,
        ordering: "due_date",
      });
      setList(data.results);
      setCount(data.count);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao listar");
    } finally {
      setLoading(false);
    }
  }, [page, search, filterStatus, filterCustomer, dueFrom, dueTo]);

  useEffect(() => {
    void load();
  }, [load]);

  const linesTotal = useMemo(
    () => form.lines.reduce((s, ln) => s + lineMoney(ln.quantity, ln.unit_price, ln.discount), 0),
    [form.lines],
  );

  const buildPayload = (): Record<string, unknown> => {
    const customer = form.customer === "" ? null : Number(form.customer);
    const lines = form.lines
      .filter((ln) => ln.product.trim())
      .map((ln) => ({
        product: Number(ln.product),
        quantity: ln.quantity.trim(),
        unit: ln.unit,
        unit_price: ln.unit_price.trim(),
        discount: ln.discount.trim() || "0",
      }));
    if (!lines.length) {
      throw new Error("Inclua ao menos uma linha com produto.");
    }
    for (let i = 0; i < lines.length; i++) {
      const ln = lines[i];
      const q = parseDecimal(String(ln.quantity));
      const up = parseDecimal(String(ln.unit_price));
      const disc = parseDecimal(String(ln.discount ?? "0")) ?? 0;
      if (q === null || q <= 0) {
        throw new Error(`Linha ${i + 1}: quantidade deve ser maior que zero.`);
      }
      if (up === null || up <= 0) {
        throw new Error(`Linha ${i + 1}: preço unitário deve ser maior que zero.`);
      }
      if (disc < 0) {
        throw new Error(`Linha ${i + 1}: desconto não pode ser negativo.`);
      }
      if (q * up - disc < -0.0001) {
        throw new Error(`Linha ${i + 1}: total da linha não pode ser negativo.`);
      }
    }
    const payload: Record<string, unknown> = {
      customer,
      description: form.description.trim(),
      issue_date: form.issue_date,
      due_date: form.due_date,
      status: form.status,
      notes: form.notes.trim(),
      lines,
    };
    if (form.status === "paid") {
      if (!form.received_at) {
        throw new Error("Informe a data efetiva do recebimento ao marcar como recebido.");
      }
      payload.received_at = form.received_at;
    }
    return payload;
  };

  const submitForm = async () => {
    if (!form.description.trim() || !form.due_date) {
      setErr("Preencha descrição e vencimento.");
      return;
    }
    setSaving(true);
    setErr(null);
    try {
      const payload = buildPayload();
      if (editing) {
        await updateAccountReceivable(editing.id, payload);
      } else {
        await createAccountReceivable(payload);
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

  const startEdit = (row: AccountReceivable) => {
    setEditing(row);
    const lines =
      row.lines && row.lines.length > 0 ? row.lines.map(mapApiLineToForm) : [emptyLine()];
    setForm({
      customer: row.customer != null ? String(row.customer) : "",
      description: row.description,
      issue_date: row.issue_date ?? todayLocal(),
      due_date: row.due_date,
      status: row.status,
      received_at: row.received_at ?? "",
      notes: row.notes,
      lines,
    });
  };

  const cancelForm = () => {
    setEditing(null);
    setForm(emptyForm);
  };

  const handleDelete = async (row: AccountReceivable) => {
    setErr(null);
    try {
      await deleteAccountReceivable(row.id);
      if (editing?.id === row.id) cancelForm();
      await load();
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Erro ao excluir");
    }
  };

  const updateLine = (idx: number, patch: Partial<LineForm>) => {
    setForm((f) => {
      const lines = [...f.lines];
      const cur = { ...lines[idx], ...patch };
      if (patch.product != null) {
        const p = products.find((x) => String(x.id) === cur.product);
        if (p) {
          const u = coerceProductUnitCode(p.unit);
          cur.unit = compatibleUnitsForProduct(u).includes(cur.unit)
            ? cur.unit
            : compatibleUnitsForProduct(u)[0] ?? DEFAULT_PRODUCT_UNIT;
        }
      }
      lines[idx] = cur;
      return { ...f, lines };
    });
  };

  const addLine = () => setForm((f) => ({ ...f, lines: [...f.lines, emptyLine()] }));
  const removeLine = (idx: number) =>
    setForm((f) => ({
      ...f,
      lines: f.lines.length > 1 ? f.lines.filter((_, i) => i !== idx) : f.lines,
    }));

  const columns: ColumnsType<AccountReceivable> = useMemo(
    () => [
      { title: "Emissão", dataIndex: "issue_date", key: "issue_date", width: 110 },
      { title: "Vencimento", dataIndex: "due_date", key: "due_date", width: 110 },
      { title: "Descrição", dataIndex: "description", key: "description" },
      { title: "Cliente", dataIndex: "customer_name", key: "customer_name", render: (v) => v ?? "—" },
      {
        title: "Linhas",
        key: "nlines",
        width: 72,
        render: (_: unknown, r: AccountReceivable) => r.lines?.length ?? 0,
      },
      { title: "Total R$", dataIndex: "amount", key: "amount", width: 100 },
      {
        title: "Status",
        dataIndex: "status",
        key: "status",
        width: 110,
        render: (s: ReceivableStatus) => STATUS_LABEL[s],
      },
      { title: "Recebido em", dataIndex: "received_at", key: "received_at", render: (v) => v ?? "—" },
      {
        title: "Ações",
        key: "actions",
        width: 96,
        render: (_, row) => (
          <Space size={4}>
            <Tooltip title="Editar">
              <Button
                type="text"
                icon={<EditOutlined />}
                aria-label="Editar"
                onClick={() => startEdit(row)}
              />
            </Tooltip>
            <Tooltip title="Excluir">
              <Popconfirm
                title={`Excluir "${row.description}"?`}
                okText="Excluir"
                cancelText="Cancelar"
                okButtonProps={{ danger: true }}
                onConfirm={() => void handleDelete(row)}
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
        Contas a receber
      </Typography.Title>
      <Typography.Paragraph type="secondary">
        Um lançamento pode ter várias linhas (produtos) para o mesmo cliente. O total é a soma das
        linhas (quantidade × preço − desconto).
      </Typography.Paragraph>

      <Card size="small" title="Filtros">
        <Space wrap>
          <Input
            placeholder="Buscar descrição ou observações"
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
            placeholder="Status"
            value={filterStatus || undefined}
            onChange={(v) => {
              setFilterStatus(v ?? "");
              setPage(1);
            }}
            allowClear
            style={{ width: 160 }}
            options={[
              { value: "open", label: "Em aberto" },
              { value: "paid", label: "Recebido" },
              { value: "cancelled", label: "Cancelado" },
            ]}
          />
          <Select
            placeholder="Cliente"
            value={filterCustomer || undefined}
            onChange={(v) => {
              setFilterCustomer(v ?? "");
              setPage(1);
            }}
            allowClear
            showSearch
            optionFilterProp="label"
            style={{ width: 220 }}
            options={customers.map((c) => ({ value: String(c.id), label: c.name }))}
          />
          <DatePicker
            placeholder="Venc. de"
            format="YYYY-MM-DD"
            value={dueFrom ? dayjs(dueFrom) : null}
            onChange={(_, s) => {
              setDueFrom(typeof s === "string" ? s : "");
              setPage(1);
            }}
          />
          <DatePicker
            placeholder="Venc. até"
            format="YYYY-MM-DD"
            value={dueTo ? dayjs(dueTo) : null}
            onChange={(_, s) => {
              setDueTo(typeof s === "string" ? s : "");
              setPage(1);
            }}
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
        title={editing ? "Editar lançamento" : "Novo lançamento"}
        extra={
          editing || form.description ? (
            <Button type="link" onClick={cancelForm}>
              Cancelar
            </Button>
          ) : null
        }
      >
        <Form layout="vertical" onFinish={() => void submitForm()}>
          <Space wrap size="middle" style={{ width: "100%" }}>
            <Form.Item label="Cliente" style={{ minWidth: 220, marginBottom: 0 }}>
              <Select
                allowClear
                placeholder="—"
                value={form.customer || undefined}
                onChange={(v) => setForm((f) => ({ ...f, customer: v ?? "" }))}
                options={customers.map((c) => ({ value: String(c.id), label: c.name }))}
                showSearch
                optionFilterProp="label"
                style={{ width: 260 }}
              />
            </Form.Item>
            <Form.Item label="Descrição *" required style={{ minWidth: 260, marginBottom: 0, flex: 1 }}>
              <Input
                value={form.description}
                onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              />
            </Form.Item>
            <Form.Item label="Emissão *" required style={{ marginBottom: 0 }}>
              <DatePicker
                format="YYYY-MM-DD"
                style={{ width: "100%" }}
                value={form.issue_date ? dayjs(form.issue_date) : null}
                onChange={(_, s) =>
                  setForm((f) => ({ ...f, issue_date: typeof s === "string" ? s : "" }))
                }
              />
            </Form.Item>
            <Form.Item label="Vencimento *" required style={{ marginBottom: 0 }}>
              <DatePicker
                format="YYYY-MM-DD"
                style={{ width: "100%" }}
                value={form.due_date ? dayjs(form.due_date) : null}
                onChange={(_, s) => setForm((f) => ({ ...f, due_date: typeof s === "string" ? s : "" }))}
              />
            </Form.Item>
            <Form.Item label="Status" style={{ minWidth: 160, marginBottom: 0 }}>
              <Select
                value={form.status}
                onChange={(status) => {
                  const s = status as ReceivableStatus;
                  setForm((f) => ({
                    ...f,
                    status: s,
                    received_at: s === "paid" && !f.received_at ? todayLocal() : f.received_at,
                  }));
                }}
                options={[
                  { value: "open", label: "Em aberto" },
                  { value: "paid", label: "Recebido" },
                  { value: "cancelled", label: "Cancelado" },
                ]}
              />
            </Form.Item>
            {form.status === "paid" ? (
              <Form.Item label="Recebido em *" required style={{ marginBottom: 0 }}>
                <DatePicker
                  format="YYYY-MM-DD"
                  style={{ width: "100%" }}
                  value={form.received_at ? dayjs(form.received_at) : null}
                  onChange={(_, s) =>
                    setForm((f) => ({ ...f, received_at: typeof s === "string" ? s : "" }))
                  }
                />
              </Form.Item>
            ) : null}
          </Space>

          <Typography.Text strong style={{ display: "block", marginTop: 12 }}>
            Itens (linhas)
          </Typography.Text>
          <Space direction="vertical" style={{ width: "100%" }} size="small">
            {form.lines.map((ln, idx) => {
              const p = products.find((x) => String(x.id) === ln.product);
              const unitOpts = p
                ? PRODUCT_UNIT_OPTIONS.filter((o) =>
                    compatibleUnitsForProduct(coerceProductUnitCode(p.unit)).includes(o.value),
                  )
                : PRODUCT_UNIT_OPTIONS;
              const sub = lineMoney(ln.quantity, ln.unit_price, ln.discount);
              return (
                <Space key={idx} wrap style={{ width: "100%", alignItems: "flex-start" }}>
                  <Select
                    placeholder="Produto *"
                    value={ln.product || undefined}
                    onChange={(v) => updateLine(idx, { product: v ?? "" })}
                    showSearch
                    optionFilterProp="label"
                    style={{ minWidth: 220, flex: 1 }}
                    options={products.map((x) => ({
                      value: String(x.id),
                      label: `${x.sku} — ${x.name}`,
                    }))}
                  />
                  <Input
                    style={{ width: 88 }}
                    inputMode="decimal"
                    placeholder="Qtd"
                    value={ln.quantity}
                    onChange={(e) => updateLine(idx, { quantity: e.target.value })}
                  />
                  <Select<ProductUnitCode>
                    style={{ width: 120 }}
                    value={ln.unit}
                    onChange={(v) => updateLine(idx, { unit: v })}
                    options={unitOpts}
                  />
                  <Input
                    style={{ width: 100 }}
                    inputMode="decimal"
                    placeholder="Preço"
                    value={ln.unit_price}
                    onChange={(e) => updateLine(idx, { unit_price: e.target.value })}
                  />
                  <Input
                    style={{ width: 88 }}
                    inputMode="decimal"
                    placeholder="Desc."
                    value={ln.discount}
                    onChange={(e) => updateLine(idx, { discount: e.target.value })}
                  />
                  <Typography.Text type="secondary" style={{ minWidth: 72 }}>
                    = R$ {sub.toFixed(2)}
                  </Typography.Text>
                  <Button
                    type="text"
                    danger
                    icon={<MinusCircleOutlined />}
                    onClick={() => removeLine(idx)}
                    disabled={form.lines.length <= 1}
                  />
                </Space>
              );
            })}
            <Button type="dashed" icon={<PlusOutlined />} onClick={addLine}>
              Adicionar linha
            </Button>
          </Space>

          <Typography.Text style={{ display: "block", marginTop: 8 }}>
            Total do documento: <strong>R$ {linesTotal.toFixed(2)}</strong> (gravado ao salvar)
          </Typography.Text>

          <Form.Item label="Observações" style={{ marginTop: 8 }}>
            <Input.TextArea
              value={form.notes}
              onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
              rows={2}
            />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={saving}>
            {editing ? "Salvar" : "Criar"}
          </Button>
        </Form>
      </Card>

      {err ? <Alert type="error" message={err} showIcon /> : null}

      <Spin spinning={loading}>
        <Table<AccountReceivable>
          rowKey="id"
          columns={columns}
          dataSource={list}
          pagination={false}
          scroll={{ x: true }}
        />
        <PaginationBar page={page} totalCount={count} pageSize={PAGE_SIZE} onPageChange={setPage} />
      </Spin>
    </Space>
  );
}
