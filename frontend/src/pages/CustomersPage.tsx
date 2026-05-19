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
import {
  createCustomer,
  deleteCustomer,
  listCustomers,
  updateCustomer,
} from "../api/catalog";
import type { Customer } from "../types/catalog";
import type { ColumnsType } from "antd/es/table";

const PAGE_SIZE = 20;

const emptyForm = {
  name: "",
  document: "",
  phone: "",
  email: "",
  address: "",
  is_active: true,
};

export function CustomersPage() {
  const [list, setList] = useState<Customer[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [filterActive, setFilterActive] = useState("");
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [editing, setEditing] = useState<Customer | null>(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const data = await listCustomers({
        page,
        search: search || undefined,
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
  }, [page, search, filterActive]);

  useEffect(() => {
    void load();
  }, [load]);

  const submitForm = async () => {
    if (!form.name.trim()) return;
    setSaving(true);
    setErr(null);
    try {
      const payload = {
        name: form.name.trim(),
        document: form.document.trim(),
        phone: form.phone.trim(),
        email: form.email.trim(),
        address: form.address.trim(),
        is_active: form.is_active,
      };
      if (editing) {
        await updateCustomer(editing.id, payload);
      } else {
        await createCustomer(payload);
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

  const startEdit = (c: Customer) => {
    setEditing(c);
    setForm({
      name: c.name,
      document: c.document,
      phone: c.phone,
      email: c.email,
      address: c.address,
      is_active: c.is_active,
    });
  };

  const cancelForm = () => {
    setEditing(null);
    setForm(emptyForm);
  };

  const handleDelete = async (c: Customer) => {
    setErr(null);
    try {
      await deleteCustomer(c.id);
      if (editing?.id === c.id) cancelForm();
      await load();
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Erro ao excluir");
    }
  };

  const columns: ColumnsType<Customer> = useMemo(
    () => [
      { title: "Nome", dataIndex: "name", key: "name" },
      { title: "Documento", dataIndex: "document", key: "document" },
      { title: "Telefone", dataIndex: "phone", key: "phone" },
      { title: "E-mail", dataIndex: "email", key: "email" },
      {
        title: "Ativo",
        dataIndex: "is_active",
        key: "is_active",
        width: 90,
        render: (v: boolean) => (v ? "Sim" : "Não"),
      },
      {
        title: "Ações",
        key: "actions",
        width: 96,
        render: (_, c) => (
          <Space size={4}>
            <Tooltip title="Editar">
              <Button
                type="text"
                icon={<EditOutlined />}
                aria-label="Editar"
                onClick={() => startEdit(c)}
              />
            </Tooltip>
            <Tooltip title="Excluir">
              <Popconfirm
                title={`Excluir cliente "${c.name}"?`}
                okText="Excluir"
                cancelText="Cancelar"
                okButtonProps={{ danger: true }}
                onConfirm={() => void handleDelete(c)}
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
        Clientes
      </Typography.Title>

      <Card size="small" title="Filtros">
        <Space wrap>
          <Input
            placeholder="Buscar"
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
            placeholder="Situação"
            value={filterActive || undefined}
            onChange={(v) => {
              setFilterActive(v ?? "");
              setPage(1);
            }}
            allowClear
            style={{ width: 140 }}
            options={[
              { value: "true", label: "Ativos" },
              { value: "false", label: "Inativos" },
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
        title={editing ? "Editar cliente" : "Novo cliente"}
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
            <Form.Item label="Nome *" required style={{ minWidth: 200, marginBottom: 0 }}>
              <Input
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              />
            </Form.Item>
            <Form.Item label="CPF/CNPJ" style={{ minWidth: 160, marginBottom: 0 }}>
              <Input
                value={form.document}
                onChange={(e) => setForm((f) => ({ ...f, document: e.target.value }))}
              />
            </Form.Item>
            <Form.Item label="Telefone" style={{ minWidth: 140, marginBottom: 0 }}>
              <Input
                value={form.phone}
                onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
              />
            </Form.Item>
            <Form.Item label="E-mail" style={{ minWidth: 200, marginBottom: 0 }}>
              <Input
                type="email"
                value={form.email}
                onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
              />
            </Form.Item>
          </Space>
          <Form.Item label="Endereço" style={{ marginBottom: 8 }}>
            <Input.TextArea
              value={form.address}
              onChange={(e) => setForm((f) => ({ ...f, address: e.target.value }))}
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
        <Table<Customer> rowKey="id" columns={columns} dataSource={list} pagination={false} />
        <PaginationBar page={page} totalCount={count} pageSize={PAGE_SIZE} onPageChange={setPage} />
      </Spin>
    </Space>
  );
}
