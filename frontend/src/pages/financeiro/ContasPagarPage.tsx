import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
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
import { BarraPaginacao } from "../../components/BarraPaginacao";
import { listarTodosFornecedores } from "../../api/cadastro";
import {
  criarContaPagar,
  excluirContaPagar,
  listarContasPagar,
  atualizarContaPagar,
} from "../../api/financeiro";
import type { Fornecedor } from "../../types/cadastro";
import type { ContaPagar, SituacaoPagar } from "../../types/financeiro";
import type { ColumnsType } from "antd/es/table";
import { todayLocal } from "../../utils/data";

const PAGE_SIZE = 20;

const STATUS_LABEL: Record<SituacaoPagar, string> = {
  aberto: "Em aberto",
  parcial: "Parcial",
  pago: "Pago",
  cancelado: "Cancelado",
};

const emptyForm = {
  fornecedor: "",
  descricao: "",
  valor: "",
  vencimento: "",
  situacao: "aberto" as SituacaoPagar,
  pago_em: "",
  observacoes: "",
};

function parsePositiveAmount(raw: string | undefined): number | null {
  const t = (raw ?? "").trim().replace(",", ".");
  if (t === "") return null;
  const n = Number(t);
  if (!Number.isFinite(n)) return null;
  return n;
}

export function ContasPagarPage() {
  const [list, setList] = useState<ContaPagar[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [filterSituacao, setFilterStatus] = useState<string>("");
  const [filterFornecedor, setFilterFornecedor] = useState<string>("");
  const [filterParcelado, setFilterParcelado] = useState<string>("");
  const [dueFrom, setDueFrom] = useState("");
  const [dueTo, setDueTo] = useState("");
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [suppliers, setFornecedores] = useState<Fornecedor[]>([]);
  const [form, setForm] = useState(emptyForm);
  const [editing, setEditing] = useState<ContaPagar | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    void listarTodosFornecedores().then(setFornecedores).catch(() => {});
  }, []);

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const data = await listarContasPagar({
        page,
        search: search || undefined,
        situacao: filterSituacao || undefined,
        fornecedor: filterFornecedor || undefined,
        due_from: dueFrom || undefined,
        due_to: dueTo || undefined,
        documento_parcelado:
          filterParcelado === "sim" ? true : filterParcelado === "nao" ? false : undefined,
        ordering: "due_date",
      });
      setList(data.resultados);
      setCount(data.total);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao listar");
    } finally {
      setLoading(false);
    }
  }, [page, search, filterSituacao, filterFornecedor, filterParcelado, dueFrom, dueTo]);

  useEffect(() => {
    void load();
  }, [load]);

  const buildPayload = (): Record<string, unknown> => {
    const fornecedor = form.fornecedor === "" ? null : Number(form.fornecedor);
    const payload: Record<string, unknown> = {
      fornecedor,
      descricao: form.descricao.trim(),
      valor: form.valor.trim(),
      vencimento: form.vencimento,
      situacao: form.situacao,
      observacoes: form.observacoes.trim(),
    };
    if (form.situacao === "pago") {
      if (!form.pago_em) {
        throw new Error("Informe a data efetiva do pagamento ao marcar como pago.");
      }
      payload.pago_em = form.pago_em;
    }
    return payload;
  };

  const submitForm = async () => {
    if (!form.descricao.trim() || !form.vencimento || !form.valor.trim()) {
      setErr("Preencha descrição, vencimento e valor.");
      return;
    }
    const amt = parsePositiveAmount(form.valor);
    if (amt === null || amt <= 0) {
      setErr("Informe o valor maior que zero.");
      return;
    }
    setSaving(true);
    setErr(null);
    try {
      const payload = buildPayload();
      if (editing) {
        await atualizarContaPagar(editing.id, payload);
      } else {
        await criarContaPagar(payload);
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

  const startEdit = (row: ContaPagar) => {
    setEditing(row);
    setForm({
      fornecedor: row.fornecedor != null ? String(row.fornecedor) : "",
      descricao: row.descricao,
      valor: row.valor,
      vencimento: row.vencimento,
      situacao: row.situacao,
      pago_em: row.pago_em ?? "",
      observacoes: row.observacoes,
    });
  };

  const cancelForm = () => {
    setEditing(null);
    setForm(emptyForm);
  };

  const handleDelete = async (row: ContaPagar) => {
    setErr(null);
    try {
      await excluirContaPagar(row.id);
      if (editing?.id === row.id) cancelForm();
      await load();
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Erro ao excluir");
    }
  };

  const columns: ColumnsType<ContaPagar> = useMemo(
    () => [
      { title: "Vencimento", dataIndex: "vencimento", key: "vencimento", width: 120 },
      { title: "Descrição", dataIndex: "descricao", key: "descricao" },
      { title: "Fornecedor", dataIndex: "nome_fornecedor", key: "nome_fornecedor", render: (v) => v ?? "—" },
      { title: "Valor", dataIndex: "valor", key: "valor" },
      {
        title: "Parcela",
        key: "parcela",
        width: 90,
        render: (_, row) =>
          row.rotulo_parcela ? (
            <Link to="/app/financeiro/documentos">{row.rotulo_parcela}</Link>
          ) : (
            "—"
          ),
      },
      {
        title: "Status",
        dataIndex: "situacao",
        key: "situacao",
        render: (s: SituacaoPagar) => STATUS_LABEL[s],
      },
      { title: "Pago em", dataIndex: "pago_em", key: "pago_em", render: (v) => v ?? "—" },
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
                title={`Excluir "${row.descricao}"?`}
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
            value={filterSituacao || undefined}
            onChange={(v) => {
              setFilterStatus(v ?? "");
              setPage(1);
            }}
            allowClear
            style={{ width: 160 }}
            options={[
              { value: "aberto", label: "Em aberto" },
              { value: "parcial", label: "Parcial" },
              { value: "pago", label: "Pago" },
              { value: "cancelado", label: "Cancelado" },
            ]}
          />
          <Select
            placeholder="Parcelado"
            value={filterParcelado || undefined}
            onChange={(v) => {
              setFilterParcelado(v ?? "");
              setPage(1);
            }}
            allowClear
            style={{ width: 150 }}
            options={[
              { value: "sim", label: "Só parcelado" },
              { value: "nao", label: "Avulso" },
            ]}
          />
          <Select
            placeholder="Fornecedor"
            value={filterFornecedor || undefined}
            onChange={(v) => {
              setFilterFornecedor(v ?? "");
              setPage(1);
            }}
            allowClear
            showSearch
            optionFilterProp="label"
            style={{ width: 220 }}
            options={suppliers.map((s) => ({ value: String(s.id), label: s.nome }))}
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
          <Space size="small">
            {!editing ? (
              <Link to="/app/financeiro/documentos?novo=pagar">
                <Button type="default" size="small">
                  Parcelamento
                </Button>
              </Link>
            ) : null}
            {editing || form.descricao ? (
              <Button type="link" size="small" onClick={cancelForm}>
                Cancelar
              </Button>
            ) : null}
          </Space>
        }
      >
        <Form layout="vertical" onFinish={() => void submitForm()}>
          <Space wrap size="middle" style={{ width: "100%" }}>
            <Form.Item label="Fornecedor" style={{ minWidth: 220, marginBottom: 0 }}>
              <Select
                allowClear
                placeholder="—"
                value={form.fornecedor || undefined}
                onChange={(v) => setForm((f) => ({ ...f, fornecedor: v ?? "" }))}
                options={suppliers.map((s) => ({ value: String(s.id), label: s.nome }))}
                showSearch
                optionFilterProp="label"
                style={{ width: 260 }}
              />
            </Form.Item>
            <Form.Item label="Descrição *" required style={{ minWidth: 260, marginBottom: 0, flex: 1 }}>
              <Input
                value={form.descricao}
                onChange={(e) => setForm((f) => ({ ...f, descricao: e.target.value }))}
              />
            </Form.Item>
            <Form.Item label="Valor *" required style={{ minWidth: 120, marginBottom: 0 }}>
              <Input
                inputMode="decimal"
                value={form.valor}
                onChange={(e) => setForm((f) => ({ ...f, valor: e.target.value }))}
              />
            </Form.Item>
            <Form.Item label="Vencimento *" required style={{ marginBottom: 0 }}>
              <DatePicker
                format="YYYY-MM-DD"
                style={{ width: "100%" }}
                value={form.vencimento ? dayjs(form.vencimento) : null}
                onChange={(_, s) => setForm((f) => ({ ...f, vencimento: typeof s === "string" ? s : "" }))}
              />
            </Form.Item>
            <Form.Item label="Status" style={{ minWidth: 160, marginBottom: 0 }}>
              <Select
                value={form.situacao}
                onChange={(status) => {
                  const s = status as SituacaoPagar;
                  setForm((f) => ({
                    ...f,
                    situacao: s,
                    pago_em: s === "pago" && !f.pago_em ? todayLocal() : f.pago_em,
                  }));
                }}
                options={[
                  { value: "aberto", label: "Em aberto" },
                  { value: "pago", label: "Pago" },
                  { value: "cancelado", label: "Cancelado" },
                ]}
              />
            </Form.Item>
            {form.situacao === "pago" ? (
              <Form.Item label="Pago em *" required style={{ marginBottom: 0 }}>
                <DatePicker
                  format="YYYY-MM-DD"
                  style={{ width: "100%" }}
                  value={form.pago_em ? dayjs(form.pago_em) : null}
                  onChange={(_, s) =>
                    setForm((f) => ({ ...f, pago_em: typeof s === "string" ? s : "" }))
                  }
                />
              </Form.Item>
            ) : null}
          </Space>
          <Form.Item label="Observações">
            <Input.TextArea
              value={form.observacoes}
              onChange={(e) => setForm((f) => ({ ...f, observacoes: e.target.value }))}
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
        <Table<ContaPagar>
          rowKey="id"
          columns={columns}
          dataSource={list}
          pagination={false}
          scroll={{ x: true }}
        />
        <BarraPaginacao page={page} totalCount={count} pageSize={PAGE_SIZE} onPageChange={setPage} />
      </Spin>
    </Space>
  );
}
