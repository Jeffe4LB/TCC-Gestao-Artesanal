import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Alert,
  Button,
  Card,
  Form,
  Input,
  Popconfirm,
  Space,
  Spin,
  Table,
  Tooltip,
  Typography,
} from "antd";
import { DeleteOutlined, EditOutlined } from "@ant-design/icons";
import { PaginationBar } from "../components/PaginationBar";
import {
  createCategory,
  deleteCategory,
  listCategories,
  updateCategory,
} from "../api/catalog";
import { useToast } from "../hooks/useToast";
import type { Category } from "../types/catalog";
import type { ColumnsType } from "antd/es/table";

const PAGE_SIZE = 20;

export function CategoriesPage() {
  const { showToast } = useToast();
  const [list, setList] = useState<Category[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [formName, setFormName] = useState("");
  const [editing, setEditing] = useState<Category | null>(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const data = await listCategories({
        page,
        search: search || undefined,
        ordering: "name",
      });
      setList(data.results);
      setCount(data.count);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao listar");
    } finally {
      setLoading(false);
    }
  }, [page, search]);

  useEffect(() => {
    void load();
  }, [load]);

  const submitForm = async () => {
    if (!formName.trim()) return;
    setSaving(true);
    setErr(null);
    try {
      if (editing) {
        await updateCategory(editing.id, { name: formName.trim() });
      } else {
        await createCategory({ name: formName.trim() });
      }
      setFormName("");
      setEditing(null);
      await load();
      showToast(editing ? "Categoria atualizada." : "Categoria criada.", "success", { persist: true });
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Erro ao salvar");
    } finally {
      setSaving(false);
    }
  };

  const startEdit = (c: Category) => {
    setEditing(c);
    setFormName(c.name);
  };

  const cancelForm = () => {
    setEditing(null);
    setFormName("");
  };

  const handleDelete = async (c: Category) => {
    setErr(null);
    try {
      await deleteCategory(c.id);
      if (editing?.id === c.id) cancelForm();
      await load();
      showToast("Categoria excluída.", "success", { persist: true });
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Erro ao excluir");
    }
  };

  const columns: ColumnsType<Category> = useMemo(
    () => [
      { title: "Nome", dataIndex: "name", key: "name" },
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
                title={`Excluir categoria "${c.name}"?`}
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
        Categorias
      </Typography.Title>

      <Card size="small" title="Buscar">
        <Form layout="inline" onFinish={() => { setPage(1); setSearch(searchInput.trim()); }}>
          <Form.Item>
            <Input
              placeholder="Buscar por nome"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              allowClear
              onPressEnter={() => {
                setPage(1);
                setSearch(searchInput.trim());
              }}
            />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit">
              Buscar
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Card
        size="small"
        title={editing ? "Editar categoria" : "Nova categoria"}
        extra={
          editing ? (
            <Button type="link" onClick={cancelForm}>
              Cancelar edição
            </Button>
          ) : null
        }
      >
        <Form layout="vertical" onFinish={() => void submitForm()}>
          <Space wrap>
            <Form.Item label="Nome" required style={{ marginBottom: 0, minWidth: 240 }}>
              <Input
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                placeholder="Nome da categoria"
              />
            </Form.Item>
            <Button type="primary" htmlType="submit" loading={saving}>
              Salvar
            </Button>
          </Space>
        </Form>
      </Card>

      {err ? <Alert type="error" message={err} showIcon /> : null}

      <Spin spinning={loading}>
        <Table<Category>
          rowKey="id"
          columns={columns}
          dataSource={list}
          pagination={false}
        />
        <PaginationBar page={page} totalCount={count} pageSize={PAGE_SIZE} onPageChange={setPage} />
      </Spin>
    </Space>
  );
}
