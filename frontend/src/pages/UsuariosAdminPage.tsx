import { useCallback, useEffect, useState } from "react";
import {
  Alert,
  Button,
  Card,
  Checkbox,
  Form,
  Grid,
  Input,
  Modal,
  Popconfirm,
  message,
  Select,
  Space,
  Spin,
  Switch,
  Table,
  Tooltip,
  Typography,
} from "antd";
import { DeleteOutlined, EditOutlined, KeyOutlined, PlusOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import {
  atualizarUsuarioAdmin,
  criarUsuarioAdmin,
  excluirUsuarioAdmin,
  listarUsuariosAdmin,
  resetarSenhaUsuarioAdmin,
  type LinhaUsuarioAdmin,
} from "../api/usuariosAdmin";
import { useAutenticacao } from "../hooks/useAutenticacao";
import { useToast } from "../hooks/useToast";
import { ROTULOS_PAPEL, type PapelUsuario } from "../types/autenticacao";

const ROTULOS_COLABORADOR: Record<string, string> = {
  colaborador_dados_mestres: "Cadastros (categorias, fornecedores, produtos, clientes)",
  colaborador_estoque_leitura: "Ver saldos e alertas de estoque",
  colaborador_estoque_movimentacoes: "Movimentações de estoque",
  colaborador_receitas_producao: "Receitas e produção",
  colaborador_financeiro: "Financeiro (pagar, receber, fluxo, alertas)",
  colaborador_relatorios: "Relatórios",
  colaborador_painel: "Painel (indicadores e resumos)",
};

const CHAVES_COLABORADOR = [
  "colaborador_dados_mestres",
  "colaborador_estoque_leitura",
  "colaborador_estoque_movimentacoes",
  "colaborador_receitas_producao",
  "colaborador_financeiro",
  "colaborador_relatorios",
  "colaborador_painel",
] as const;

const DEFAULTS_COLABORADOR_NOVO: Record<(typeof CHAVES_COLABORADOR)[number], boolean> = {
  colaborador_dados_mestres: false,
  colaborador_estoque_leitura: true,
  colaborador_estoque_movimentacoes: true,
  colaborador_receitas_producao: false,
  colaborador_financeiro: true,
  colaborador_relatorios: false,
  colaborador_painel: true,
};

export function UsuariosAdminPage() {
  const screens = Grid.useBreakpoint();
  const modalWidth = screens.xs ? "min(100vw - 16px, 560px)" : 560;

  const { user, refreshUser } = useAutenticacao();
  const { showToast } = useToast();
  const [rows, setRows] = useState<LinhaUsuarioAdmin[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [editing, setEditing] = useState<LinhaUsuarioAdmin | null>(null);
  const [creating, setCreating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [resettingId, setResettingId] = useState<number | null>(null);
  const [form] = Form.useForm();
  const [formNovo] = Form.useForm();

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const data = await listarUsuariosAdmin();
      setRows(data);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao carregar usuários");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const openEdit = (row: LinhaUsuarioAdmin) => {
    setEditing(row);
    form.setFieldsValue({
      email: row.email,
      ativo: row.ativo,
      papel: row.papel,
      colaborador_dados_mestres: row.colaborador_dados_mestres,
      colaborador_estoque_leitura: row.colaborador_estoque_leitura,
      colaborador_estoque_movimentacoes: row.colaborador_estoque_movimentacoes,
      colaborador_receitas_producao: row.colaborador_receitas_producao,
      colaborador_financeiro: row.colaborador_financeiro,
      colaborador_relatorios: row.colaborador_relatorios,
      colaborador_painel: row.colaborador_painel,
    });
  };

  const openNovo = () => {
    setCreating(true);
    formNovo.setFieldsValue({
      nome: "",
      email: "",
      papel: "collaborator",
      ...DEFAULTS_COLABORADOR_NOVO,
    });
  };

  const columns: ColumnsType<LinhaUsuarioAdmin> = [
    { title: "Usuário", dataIndex: "username", key: "username" },
    { title: "E-mail", dataIndex: "email", key: "email", ellipsis: true },
    {
      title: "Perfil",
      dataIndex: "papel",
      key: "papel",
      width: 140,
      render: (r: PapelUsuario) => ROTULOS_PAPEL[r] ?? r,
    },
    {
      title: "Ativo",
      dataIndex: "ativo",
      key: "ativo",
      width: 80,
      render: (v: boolean) => (v ? "Sim" : "Não"),
    },
    {
      title: "",
      key: "actions",
      width: 148,
      render: (_, row) => (
        <Space size="middle" wrap={false}>
          <Tooltip title="Editar">
            <Button
              type="text"
              icon={<EditOutlined />}
              aria-label="Editar"
              onClick={() => openEdit(row)}
            />
          </Tooltip>
          <Popconfirm
            title="Resetar senha?"
            description="Será gerada uma senha temporária e enviada por e-mail. O usuário precisará trocá-la no próximo login."
            okText="Resetar"
            cancelText="Cancelar"
            onConfirm={async () => {
              setResettingId(row.id);
              try {
                const res = await resetarSenhaUsuarioAdmin(row.id);
                if (res.email_enviado) {
                  message.success(res.detail);
                } else {
                  message.warning(res.detail, 8);
                }
              } catch (e) {
                message.error(
                  e instanceof Error ? e.message : "Erro ao resetar senha",
                );
              } finally {
                setResettingId(null);
              }
            }}
          >
            <Tooltip title="Resetar senha">
              <Button
                type="text"
                icon={<KeyOutlined />}
                aria-label="Resetar senha"
                loading={resettingId === row.id}
              />
            </Tooltip>
          </Popconfirm>
          <Popconfirm
            title="Excluir usuário?"
            description="Esta ação não pode ser desfeita. Usuários com movimentações de estoque não podem ser excluídos."
            okText="Excluir"
            okButtonProps={{ danger: true }}
            cancelText="Cancelar"
            onConfirm={async () => {
              try {
                await excluirUsuarioAdmin(row.id);
                showToast("Usuário excluído.", "success");
                await load();
              } catch (e) {
                showToast(
                  e instanceof Error ? e.message : "Não foi possível excluir",
                  "error",
                );
              }
            }}
          >
            <Tooltip title="Excluir">
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
                aria-label="Excluir"
                disabled={row.id === user?.id}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const papelWatch = Form.useWatch("papel", form);
  const papelNovoWatch = Form.useWatch("papel", formNovo);

  return (
    <div style={{ maxWidth: "100%", overflow: "hidden" }}>
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          alignItems: "flex-start",
          justifyContent: "space-between",
          gap: 12,
          marginBottom: 8,
        }}
      >
        <div>
          <Typography.Title level={3} style={{ marginTop: 0, fontSize: screens.xs ? 20 : undefined }}>
            Usuários e permissões
          </Typography.Title>
          <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
            Crie contas, defina perfis e permissões de acesso ao sistema.
          </Typography.Paragraph>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={openNovo}>
          Novo usuário
        </Button>
      </div>

      {err ? (
        <Alert type="error" message={err} showIcon style={{ marginBottom: 16 }} />
      ) : null}

      <Card styles={{ body: { padding: screens.xs ? 12 : undefined } }}>
        {loading ? (
          <Spin />
        ) : (
          <Table
            rowKey="id"
            columns={columns}
            dataSource={rows}
            pagination={false}
            size={screens.xs ? "small" : "middle"}
            scroll={{ x: 748 }}
            tableLayout="fixed"
          />
        )}
      </Card>

      <Modal
        title={`Editar — ${editing?.username ?? ""}`}
        open={!!editing}
        onCancel={() => {
          setEditing(null);
          form.resetFields();
        }}
        footer={null}
        destroyOnClose
        width={modalWidth}
        styles={{ body: { maxHeight: "min(70vh, 520px)", overflowY: "auto" } }}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={async (values: Record<string, unknown>) => {
            if (!editing) return;
            setSaving(true);
            setErr(null);
            try {
              await atualizarUsuarioAdmin(editing.id, {
                email: String(values.email ?? ""),
                ativo: Boolean(values.ativo),
                papel: values.papel as PapelUsuario,
                colaborador_dados_mestres: Boolean(values.colaborador_dados_mestres),
                colaborador_estoque_leitura: Boolean(values.colaborador_estoque_leitura),
                colaborador_estoque_movimentacoes: Boolean(values.colaborador_estoque_movimentacoes),
                colaborador_receitas_producao: Boolean(values.colaborador_receitas_producao),
                colaborador_financeiro: Boolean(values.colaborador_financeiro),
                colaborador_relatorios: Boolean(values.colaborador_relatorios),
                colaborador_painel: Boolean(values.colaborador_painel),
              });
              if (editing.id === user?.id) await refreshUser();
              setEditing(null);
              form.resetFields();
              showToast("Usuário atualizado.", "success");
              await load();
            } catch (e) {
              setErr(e instanceof Error ? e.message : "Erro ao salvar");
            } finally {
              setSaving(false);
            }
          }}
        >
          <Form.Item label="E-mail" name="email" rules={[{ type: "email" }]}>
            <Input />
          </Form.Item>
          <Form.Item label="Conta ativa" name="ativo" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item
            label="Perfil"
            name="papel"
            rules={[{ required: true, message: "Selecione o perfil" }]}
          >
            <Select
              options={[
                { value: "admin", label: ROTULOS_PAPEL.admin },
                { value: "entrepreneur", label: ROTULOS_PAPEL.entrepreneur },
                { value: "collaborator", label: ROTULOS_PAPEL.collaborator },
              ]}
            />
          </Form.Item>

          {papelWatch === "collaborator" ? (
            <>
              <Typography.Text strong style={{ display: "block", marginBottom: 8 }}>
                Permissões do colaborador
              </Typography.Text>
              {CHAVES_COLABORADOR.map((key) => (
                <Form.Item
                  key={key}
                  name={key}
                  valuePropName="checked"
                  style={{ marginBottom: 4 }}
                >
                  <Checkbox>{ROTULOS_COLABORADOR[key]}</Checkbox>
                </Form.Item>
              ))}
            </>
          ) : null}

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={saving}>
                Salvar
              </Button>
              <Button
                onClick={() => {
                  setEditing(null);
                  form.resetFields();
                }}
              >
                Cancelar
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="Novo usuário"
        open={creating}
        onCancel={() => {
          setCreating(false);
          formNovo.resetFields();
        }}
        footer={null}
        destroyOnClose
        width={modalWidth}
        styles={{ body: { maxHeight: "min(70vh, 520px)", overflowY: "auto" } }}
      >
        <Form
          form={formNovo}
          layout="vertical"
          onFinish={async (values: Record<string, unknown>) => {
            setSaving(true);
            setErr(null);
            try {
              await criarUsuarioAdmin({
                nome: String(values.nome ?? ""),
                email: String(values.email ?? ""),
                papel: values.papel as PapelUsuario,
                colaborador_dados_mestres: Boolean(values.colaborador_dados_mestres),
                colaborador_estoque_leitura: Boolean(values.colaborador_estoque_leitura),
                colaborador_estoque_movimentacoes: Boolean(values.colaborador_estoque_movimentacoes),
                colaborador_receitas_producao: Boolean(values.colaborador_receitas_producao),
                colaborador_financeiro: Boolean(values.colaborador_financeiro),
                colaborador_relatorios: Boolean(values.colaborador_relatorios),
                colaborador_painel: Boolean(values.colaborador_painel),
              });
              setCreating(false);
              formNovo.resetFields();
              showToast(
                "Usuário criado. As credenciais foram enviadas por e-mail.",
                "success",
              );
              await load();
            } catch (e) {
              setErr(e instanceof Error ? e.message : "Erro ao criar usuário");
            } finally {
              setSaving(false);
            }
          }}
        >
          <Form.Item
            label="Nome"
            name="nome"
            rules={[{ required: true, message: "Informe o nome" }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            label="E-mail"
            name="email"
            rules={[
              { required: true, message: "Informe o e-mail" },
              { type: "email", message: "E-mail inválido" },
            ]}
          >
            <Input placeholder="Será usado como login" />
          </Form.Item>
          <Form.Item
            label="Perfil"
            name="papel"
            rules={[{ required: true, message: "Selecione o perfil" }]}
          >
            <Select
              options={[
                { value: "admin", label: ROTULOS_PAPEL.admin },
                { value: "entrepreneur", label: ROTULOS_PAPEL.entrepreneur },
                { value: "collaborator", label: ROTULOS_PAPEL.collaborator },
              ]}
            />
          </Form.Item>

          {papelNovoWatch === "collaborator" ? (
            <>
              <Typography.Text strong style={{ display: "block", marginBottom: 8 }}>
                Permissões do colaborador
              </Typography.Text>
              {CHAVES_COLABORADOR.map((key) => (
                <Form.Item
                  key={key}
                  name={key}
                  valuePropName="checked"
                  style={{ marginBottom: 4 }}
                >
                  <Checkbox>{ROTULOS_COLABORADOR[key]}</Checkbox>
                </Form.Item>
              ))}
            </>
          ) : null}

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={saving}>
                Criar e enviar e-mail
              </Button>
              <Button
                onClick={() => {
                  setCreating(false);
                  formNovo.resetFields();
                }}
              >
                Cancelar
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
