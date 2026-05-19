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
  Select,
  Space,
  Spin,
  Switch,
  Table,
  Tooltip,
  Typography,
} from "antd";
import { EditOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import {
  listAdminUsers,
  patchAdminUser,
  type AdminUserRow,
} from "../api/adminUsers";
import { useAuth } from "../hooks/useAuth";
import { ROLE_LABELS, type UserRole } from "../types/auth";

const COLLAB_LABELS: Record<string, string> = {
  collab_master_data: "Cadastros (categorias, fornecedores, produtos, clientes)",
  collab_stock_read: "Ver saldos e alertas de estoque",
  collab_stock_movements: "Movimentações de estoque",
  collab_recipes_production: "Receitas (BOM) e produção",
  collab_finance: "Financeiro (pagar, receber, fluxo, alertas)",
  collab_reports: "Relatórios",
  collab_dashboard: "Dashboard / painel",
};

export function UsersAdminPage() {
  const screens = Grid.useBreakpoint();
  const modalWidth = screens.xs ? "min(100vw - 16px, 560px)" : 560;

  const { user, refreshUser } = useAuth();
  const [rows, setRows] = useState<AdminUserRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [editing, setEditing] = useState<AdminUserRow | null>(null);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const data = await listAdminUsers();
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

  const openEdit = (row: AdminUserRow) => {
    setEditing(row);
    form.setFieldsValue({
      email: row.email,
      is_active: row.is_active,
      role: row.role,
      collab_master_data: row.collab_master_data,
      collab_stock_read: row.collab_stock_read,
      collab_stock_movements: row.collab_stock_movements,
      collab_recipes_production: row.collab_recipes_production,
      collab_finance: row.collab_finance,
      collab_reports: row.collab_reports,
      collab_dashboard: row.collab_dashboard,
    });
  };

  const columns: ColumnsType<AdminUserRow> = [
    { title: "Usuário", dataIndex: "username", key: "username" },
    { title: "E-mail", dataIndex: "email", key: "email", ellipsis: true },
    {
      title: "Perfil",
      dataIndex: "role",
      key: "role",
      width: 140,
      render: (r: UserRole) => ROLE_LABELS[r] ?? r,
    },
    {
      title: "Ativo",
      dataIndex: "is_active",
      key: "is_active",
      width: 80,
      render: (v: boolean) => (v ? "Sim" : "Não"),
    },
    {
      title: "",
      key: "actions",
      width: 56,
      render: (_, row) => (
        <Tooltip title="Editar">
          <Button
            type="text"
            icon={<EditOutlined />}
            aria-label="Editar"
            onClick={() => openEdit(row)}
          />
        </Tooltip>
      ),
    },
  ];

  const role = Form.useWatch("role", form);

  return (
    <div style={{ maxWidth: "100%", overflow: "hidden" }}>
      <Typography.Title level={3} style={{ marginTop: 0, fontSize: screens.xs ? 20 : undefined }}>
        Usuários e permissões
      </Typography.Title>
      <Typography.Paragraph type="secondary">
        Defina perfis e permissões de acesso ao sistema.
      </Typography.Paragraph>

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
            scroll={{ x: 640 }}
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
              await patchAdminUser(editing.id, {
                email: String(values.email ?? ""),
                is_active: Boolean(values.is_active),
                role: values.role as UserRole,
                collab_master_data: Boolean(values.collab_master_data),
                collab_stock_read: Boolean(values.collab_stock_read),
                collab_stock_movements: Boolean(values.collab_stock_movements),
                collab_recipes_production: Boolean(values.collab_recipes_production),
                collab_finance: Boolean(values.collab_finance),
                collab_reports: Boolean(values.collab_reports),
                collab_dashboard: Boolean(values.collab_dashboard),
              });
              if (editing.id === user?.id) await refreshUser();
              setEditing(null);
              form.resetFields();
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
          <Form.Item label="Conta ativa" name="is_active" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item
            label="Perfil"
            name="role"
            rules={[{ required: true, message: "Selecione o perfil" }]}
          >
            <Select
              options={[
                { value: "admin", label: ROLE_LABELS.admin },
                { value: "entrepreneur", label: ROLE_LABELS.entrepreneur },
                { value: "collaborator", label: ROLE_LABELS.collaborator },
              ]}
            />
          </Form.Item>

          {role === "collaborator" ? (
            <>
              <Typography.Text strong style={{ display: "block", marginBottom: 8 }}>
                Permissões do colaborador
              </Typography.Text>
              {(
                [
                  "collab_master_data",
                  "collab_stock_read",
                  "collab_stock_movements",
                  "collab_recipes_production",
                  "collab_finance",
                  "collab_reports",
                  "collab_dashboard",
                ] as const
              ).map((key) => (
                <Form.Item
                  key={key}
                  name={key}
                  valuePropName="checked"
                  style={{ marginBottom: 4 }}
                >
                  <Checkbox>{COLLAB_LABELS[key]}</Checkbox>
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
    </div>
  );
}
