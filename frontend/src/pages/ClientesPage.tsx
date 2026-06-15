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
import { DeleteOutlined, EditOutlined, HistoryOutlined } from "@ant-design/icons";
import { BarraPaginacao } from "../components/BarraPaginacao";
import { HistoricoParceiroDrawer } from "../components/cadastro/HistoricoParceiroDrawer";
import {
  criarCliente,
  excluirCliente,
  listarClientes,
  atualizarCliente,
} from "../api/cadastro";
import { useAutenticacao } from "../hooks/useAutenticacao";
import type { Cliente } from "../types/cadastro";
import type { ColumnsType } from "antd/es/table";

const PAGE_SIZE = 20;

const emptyForm = {
  nome: "",
  documento: "",
  telefone: "",
  email: "",
  endereco: "",
  ativo: true,
};

export function ClientesPage() {
  const { user } = useAutenticacao();
  const podeVerHistorico = user?.capacidades.financeiro ?? false;
  const [list, setList] = useState<Cliente[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [filterAtivo, setFilterActive] = useState("");
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [editing, setEditing] = useState<Cliente | null>(null);
  const [saving, setSaving] = useState(false);
  const [historicoCliente, setHistoricoCliente] = useState<Cliente | null>(null);

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const data = await listarClientes({
        page,
        search: search || undefined,
        ativo: filterAtivo === "" ? undefined : filterAtivo === "true",
        ordering: "nome",
      });
      setList(data.resultados);
      setCount(data.total);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao listar");
    } finally {
      setLoading(false);
    }
  }, [page, search, filterAtivo]);

  useEffect(() => {
    void load();
  }, [load]);

  const submitForm = async () => {
    if (!form.nome.trim()) return;
    setSaving(true);
    setErr(null);
    try {
      const payload = {
        nome: form.nome.trim(),
        documento: form.documento.trim(),
        telefone: form.telefone.trim(),
        email: form.email.trim(),
        endereco: form.endereco.trim(),
        ativo: form.ativo,
      };
      if (editing) {
        await atualizarCliente(editing.id, payload);
      } else {
        await criarCliente(payload);
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

  const startEdit = (c: Cliente) => {
    setEditing(c);
    setForm({
      nome: c.nome,
      documento: c.documento,
      telefone: c.telefone,
      email: c.email,
      endereco: c.endereco,
      ativo: c.ativo,
    });
  };

  const cancelForm = () => {
    setEditing(null);
    setForm(emptyForm);
  };

  const handleDelete = async (c: Cliente) => {
    setErr(null);
    try {
      await excluirCliente(c.id);
      if (editing?.id === c.id) cancelForm();
      await load();
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Erro ao excluir");
    }
  };

  const columns: ColumnsType<Cliente> = useMemo(
    () => [
      { title: "Nome", dataIndex: "nome", key: "nome" },
      { title: "Documento", dataIndex: "documento", key: "documento" },
      { title: "Telefone", dataIndex: "phone", key: "phone" },
      { title: "E-mail", dataIndex: "email", key: "email" },
      {
        title: "Ativo",
        dataIndex: "ativo",
        key: "ativo",
        width: 90,
        render: (v: boolean) => (v ? "Sim" : "Não"),
      },
      {
        title: "Ações",
        key: "actions",
        width: podeVerHistorico ? 128 : 96,
        render: (_, c) => (
          <Space size={4}>
            {podeVerHistorico ? (
              <Tooltip title="Histórico financeiro">
                <Button
                  type="text"
                  icon={<HistoryOutlined />}
                  aria-label="Histórico financeiro"
                  onClick={() => setHistoricoCliente(c)}
                />
              </Tooltip>
            ) : null}
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
                title={`Excluir cliente "${c.nome}"?`}
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
    [podeVerHistorico],
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
            value={filterAtivo || undefined}
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
                value={form.nome}
                onChange={(e) => setForm((f) => ({ ...f, nome: e.target.value }))}
              />
            </Form.Item>
            <Form.Item label="CPF/CNPJ" style={{ minWidth: 160, marginBottom: 0 }}>
              <Input
                value={form.documento}
                onChange={(e) => setForm((f) => ({ ...f, documento: e.target.value }))}
              />
            </Form.Item>
            <Form.Item label="Telefone" style={{ minWidth: 140, marginBottom: 0 }}>
              <Input
                value={form.telefone}
                onChange={(e) => setForm((f) => ({ ...f, telefone: e.target.value }))}
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
              value={form.endereco}
              onChange={(e) => setForm((f) => ({ ...f, endereco: e.target.value }))}
              rows={2}
            />
          </Form.Item>
          <Checkbox
            checked={form.ativo}
            onChange={(e) => setForm((f) => ({ ...f, ativo: e.target.checked }))}
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
        <Table<Cliente> rowKey="id" columns={columns} dataSource={list} pagination={false} />
        <BarraPaginacao page={page} totalCount={count} pageSize={PAGE_SIZE} onPageChange={setPage} />
      </Spin>

      {historicoCliente ? (
        <HistoricoParceiroDrawer
          open
          onClose={() => setHistoricoCliente(null)}
          titulo={historicoCliente.nome}
          tipo="cliente"
          parceiroId={historicoCliente.id}
        />
      ) : null}
    </Space>
  );
}
