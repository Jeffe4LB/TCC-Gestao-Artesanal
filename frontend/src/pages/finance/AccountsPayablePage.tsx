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
import { DeleteOutlined, EditOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import { PaginationBar } from "../../components/PaginationBar";
import { fetchAllSuppliers } from "../../api/catalog";
import {
  createAccountPayable,
  deleteAccountPayable,
  listAccountsPayable,
  updateAccountPayable,
} from "../../api/finance";
import type { Supplier } from "../../types/catalog";
import type { AccountPayable, PayableStatus } from "../../types/finance";
import type { ColumnsType } from "antd/es/table";

const PAGE_SIZE = 20;

const STATUS_LABEL: Record<PayableStatus, string> = {
  open: "Em aberto",
  paid: "Pago",
  cancelled: "Cancelado",
};

function todayLocal(): string {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

const emptyForm = {
  supplier: "",
  description: "",
  amount: "",
  due_date: "",
  status: "open" as PayableStatus,
  paid_at: "",
  notes: "",
};

function parsePositiveAmount(raw: string | undefined): number | null {
  const t = (raw ?? "").trim().replace(",", ".");
  if (t === "") return null;
  const n = Number(t);
  if (!Number.isFinite(n)) return null;
  return n;
}

export function AccountsPayablePage() {
  const [list, setList] = useState<AccountPayable[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [filterStatus, setFilterStatus] = useState<string>("");
  const [filterSupplier, setFilterSupplier] = useState<string>("");
  const [dueFrom, setDueFrom] = useState("");
  const [dueTo, setDueTo] = useState("");
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [form, setForm] = useState(emptyForm);
  const [editing, setEditing] = useState<AccountPayable | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    void fetchAllSuppliers().then(setSuppliers).catch(() => {});
  }, []);

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const data = await listAccountsPayable({
        page,
        search: search || undefined,
        status: filterStatus || undefined,
        supplier: filterSupplier || undefined,
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
  }, [page, search, filterStatus, filterSupplier, dueFrom, dueTo]);

  useEffect(() => {
    void load();
  }, [load]);

  const buildPayload = (): Record<string, unknown> => {
    const supplier = form.supplier === "" ? null : Number(form.supplier);
    const payload: Record<string, unknown> = {
      supplier,
      description: form.description.trim(),
      amount: form.amount.trim(),
      due_date: form.due_date,
      status: form.status,
      notes: form.notes.trim(),
    };
    if (form.status === "paid") {
      if (!form.paid_at) {
        throw new Error("Informe a data efetiva do pagamento ao marcar como pago.");
      }
      payload.paid_at = form.paid_at;
    }
    return payload;
  };

  const submitForm = async () => {
    if (!form.description.trim() || !form.due_date || !form.amount.trim()) {
      setErr("Preencha descrição, vencimento e valor.");
      return;
    }
    const amt = parsePositiveAmount(form.amount);
    if (amt === null || amt <= 0) {
      setErr("Informe o valor maior que zero.");
      return;
    }
    setSaving(true);
    setErr(null);
    try {
      const payload = buildPayload();
      if (editing) {
        await updateAccountPayable(editing.id, payload);
      } else {
        await createAccountPayable(payload);
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

  const startEdit = (row: AccountPayable) => {
    setEditing(row);
    setForm({
      supplier: row.supplier != null ? String(row.supplier) : "",
      description: row.description,
      amount: row.amount,
      due_date: row.due_date,
      status: row.status,
      paid_at: row.paid_at ?? "",
      notes: row.notes,
    });
  };

  const cancelForm = () => {
    setEditing(null);
    setForm(emptyForm);
  };

  const handleDelete = async (row: AccountPayable) => {
    setErr(null);
    try {
      await deleteAccountPayable(row.id);
      if (editing?.id === row.id) cancelForm();
      await load();
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Erro ao excluir");
    }
  };

  const columns: ColumnsType<AccountPayable> = useMemo(
    () => [
      { title: "Vencimento", dataIndex: "due_date", key: "due_date", width: 120 },
      { title: "Descrição", dataIndex: "description", key: "description" },
      { title: "Fornecedor", dataIndex: "supplier_name", key: "supplier_name", render: (v) => v ?? "—" },
      { title: "Valor", dataIndex: "amount", key: "amount" },
      {
        title: "Status",
        dataIndex: "status",
        key: "status",
        render: (s: PayableStatus) => STATUS_LABEL[s],
      },
      { title: "Pago em", dataIndex: "paid_at", key: "paid_at", render: (v) => v ?? "—" },
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
        Contas a pagar
      </Typography.Title>

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
              { value: "paid", label: "Pago" },
              { value: "cancelled", label: "Cancelado" },
            ]}
          />
          <Select
            placeholder="Fornecedor"
            value={filterSupplier || undefined}
            onChange={(v) => {
              setFilterSupplier(v ?? "");
              setPage(1);
            }}
            allowClear
            showSearch
            optionFilterProp="label"
            style={{ width: 220 }}
            options={suppliers.map((s) => ({ value: String(s.id), label: s.name }))}
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
            <Form.Item label="Fornecedor" style={{ minWidth: 220, marginBottom: 0 }}>
              <Select
                allowClear
                placeholder="—"
                value={form.supplier || undefined}
                onChange={(v) => setForm((f) => ({ ...f, supplier: v ?? "" }))}
                options={suppliers.map((s) => ({ value: String(s.id), label: s.name }))}
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
            <Form.Item label="Valor *" required style={{ minWidth: 120, marginBottom: 0 }}>
              <Input
                inputMode="decimal"
                value={form.amount}
                onChange={(e) => setForm((f) => ({ ...f, amount: e.target.value }))}
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
                  const s = status as PayableStatus;
                  setForm((f) => ({
                    ...f,
                    status: s,
                    paid_at: s === "paid" && !f.paid_at ? todayLocal() : f.paid_at,
                  }));
                }}
                options={[
                  { value: "open", label: "Em aberto" },
                  { value: "paid", label: "Pago" },
                  { value: "cancelled", label: "Cancelado" },
                ]}
              />
            </Form.Item>
            {form.status === "paid" ? (
              <Form.Item label="Pago em *" required style={{ marginBottom: 0 }}>
                <DatePicker
                  format="YYYY-MM-DD"
                  style={{ width: "100%" }}
                  value={form.paid_at ? dayjs(form.paid_at) : null}
                  onChange={(_, s) =>
                    setForm((f) => ({ ...f, paid_at: typeof s === "string" ? s : "" }))
                  }
                />
              </Form.Item>
            ) : null}
          </Space>
          <Form.Item label="Observações">
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
        <Table<AccountPayable>
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
