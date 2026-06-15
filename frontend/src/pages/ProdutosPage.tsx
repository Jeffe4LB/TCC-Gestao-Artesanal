import { useCallback, useEffect, useMemo, useState } from "react";
import { Alert, Button, Popconfirm, Space, Spin, Table, Tooltip, Typography } from "antd";
import { FiltrosProduto } from "../components/produtos/FiltrosProduto";
import { FormularioProduto, formProdutoVazio } from "../components/produtos/FormularioProduto";
import { DeleteOutlined, EditOutlined } from "@ant-design/icons";
import { BarraPaginacao } from "../components/BarraPaginacao";
import { formatQuantityDisplay } from "../utils/exibicaoQuantidade";
import {
  criarProduto,
  excluirProduto,
  listarTodasCategorias,
  listarTodosFornecedores,
  listarProdutos,
  atualizarProduto,
} from "../api/cadastro";
import { coerceProductUnitCode } from "../constants/unidades";
import type {
  Categoria,
  Produto,
  OrigemCustoProduto,
  TipoProduto,
  Fornecedor,
} from "../types/cadastro";
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

const costOriginLabel = (o: OrigemCustoProduto) =>
  o === "receita" ? "Receita" : "Aquisição";

export function ProdutosPage() {
  const [list, setList] = useState<Produto[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [filterCategoria, setFilterCategoria] = useState<string>("");
  const [filterTipo, setFilterType] = useState<string>("");
  const [filterAtivo, setFilterActive] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [form, setForm] = useState(formProdutoVazio);
  const [editing, setEditing] = useState<Produto | null>(null);
  const [saving, setSaving] = useState(false);
  const [categories, setCategories] = useState<Categoria[]>([]);
  const [suppliers, setFornecedores] = useState<Fornecedor[]>([]);

  useEffect(() => {
    void (async () => {
      try {
        const [cats, sups] = await Promise.all([listarTodasCategorias(), listarTodosFornecedores()]);
        setCategories(cats);
        setFornecedores(sups);
      } catch {
        /* lista de produtos ainda pode funcionar parcialmente */
      }
    })();
  }, []);

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const data = await listarProdutos({
        page,
        search: search || undefined,
        categoria: filterCategoria || undefined,
        tipo_produto: filterTipo || undefined,
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
  }, [page, search, filterCategoria, filterTipo, filterAtivo]);

  useEffect(() => {
    void load();
  }, [load]);

  const buildPayload = (): Record<string, unknown> => {
    const categoryId = form.categoria === "" ? null : Number(form.categoria);
    if (categoryId === null || Number.isNaN(categoryId)) {
      throw new Error("Selecione uma categoria");
    }
    const payload: Record<string, unknown> = {
      sku: form.sku.trim(),
      nome: form.nome.trim(),
      descricao: form.descricao.trim(),
      categoria: categoryId,
      tipo_produto: form.tipo_produto,
      unidade: form.unidade,
      preco_venda: moneyStr(form.preco_venda),
      estoque_minimo: form.estoque_minimo,
      ativo: form.ativo,
    };
    if (form.tipo_produto === "comprado") {
      payload.custo_aquisicao = moneyStr(form.custo_aquisicao);
    } else {
      payload.custo_aquisicao = "0";
    }
    if (form.fornecedor === "" || form.fornecedor === null) {
      payload.fornecedor = null;
    } else {
      payload.fornecedor = Number(form.fornecedor);
    }
    return payload;
  };

  const submitForm = async () => {
    setSaving(true);
    setErr(null);
    try {
      if (form.tipo_produto === "fabricado") {
        const sp = parsePositiveDecimal(form.preco_venda);
        if (sp === null || sp <= 0) {
          setErr("Informe o preço de venda maior que zero para produto fabricado.");
          return;
        }
      } else {
        const raw = form.preco_venda.trim();
        if (raw !== "") {
          const sp = parsePositiveDecimal(form.preco_venda);
          if (sp === null || sp < 0) {
            setErr("Preço de venda inválido ou negativo.");
            return;
          }
        }
      }
      if (form.tipo_produto === "comprado") {
        const pc = parsePositiveDecimal(form.custo_aquisicao);
        if (pc === null || pc <= 0) {
          setErr("Informe o custo de aquisição maior que zero.");
          return;
        }
      }
      const payload = buildPayload();
      if (editing) {
        await atualizarProduto(editing.id, payload);
      } else {
        await criarProduto(payload);
      }
      setForm(formProdutoVazio);
      setEditing(null);
      await load();
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Erro ao salvar");
    } finally {
      setSaving(false);
    }
  };

  const startEdit = (p: Produto) => {
    setEditing(p);
    setForm({
      sku: p.sku,
      nome: p.nome,
      descricao: p.descricao,
      categoria: p.categoria,
      fornecedor: p.fornecedor ?? "",
      tipo_produto: p.tipo_produto,
      unidade: coerceProductUnitCode(p.unidade),
      preco_venda: moneyStr(p.preco_venda ?? "0"),
      custo_aquisicao: moneyStr(p.custo_aquisicao ?? "0"),
      custo_unitario_display: moneyStr(p.custo_unitario ?? "0"),
      estoque_minimo: p.estoque_minimo,
      ativo: p.ativo,
    });
  };

  const cancelForm = () => {
    setEditing(null);
    setForm(formProdutoVazio);
  };

  const handleDelete = async (p: Produto) => {
    setErr(null);
    try {
      await excluirProduto(p.id);
      if (editing?.id === p.id) cancelForm();
      await load();
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Erro ao excluir");
    }
  };

  const columns: ColumnsType<Produto> = useMemo(
    () => [
      { title: "Código (SKU)", dataIndex: "sku", key: "sku" },
      { title: "Nome", dataIndex: "nome", key: "nome" },
      { title: "Categoria", dataIndex: "nome_categoria", key: "nome_categoria" },
      {
        title: "Tipo",
        dataIndex: "tipo_produto",
        key: "tipo_produto",
        render: (t: TipoProduto) => (t === "comprado" ? "Comprado" : "Produzido"),
      },
      { title: "Unid.", dataIndex: "unit", key: "unit", width: 56 },
      {
        title: "Venda R$",
        dataIndex: "preco_venda",
        key: "preco_venda",
        width: 88,
        render: (v: string) => moneyStr(v),
      },
      {
        title: "Custo R$",
        dataIndex: "custo_unitario",
        key: "custo_unitario",
        width: 88,
        render: (v: string) => moneyStr(v),
      },
      {
        title: "Origem custo",
        dataIndex: "origem_custo",
        key: "origem_custo",
        width: 110,
        render: (o: OrigemCustoProduto | undefined) => costOriginLabel(o ?? "aquisicao"),
      },
      {
        title: "Mín.",
        dataIndex: "estoque_minimo",
        key: "estoque_minimo",
        width: 80,
        render: (v: string) => formatQuantityDisplay(v),
      },
      {
        title: "Ativo",
        dataIndex: "ativo",
        key: "ativo",
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
                title={`Excluir produto "${p.nome}" (${p.sku})?`}
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

      <FiltrosProduto
        searchInput={searchInput}
        onSearchInputChange={setSearchInput}
        filterCategoria={filterCategoria}
        onFilterCategoriaChange={(v) => {
          setFilterCategoria(v);
          setPage(1);
        }}
        filterTipo={filterTipo}
        onFilterTipoChange={(v) => {
          setFilterType(v);
          setPage(1);
        }}
        filterAtivo={filterAtivo}
        onFilterAtivoChange={(v) => {
          setFilterActive(v);
          setPage(1);
        }}
        categories={categories}
        onBuscar={() => {
          setPage(1);
          setSearch(searchInput.trim());
        }}
      />

      <FormularioProduto
        form={form}
        editing={editing}
        saving={saving}
        categories={categories}
        suppliers={suppliers}
        onFormChange={setForm}
        onSubmit={() => void submitForm()}
        onCancel={cancelForm}
      />

      {err ? <Alert type="error" message={err} showIcon /> : null}

      <Spin spinning={loading}>
        <Table<Produto> rowKey="id" columns={columns} dataSource={list} pagination={false} />
        <BarraPaginacao page={page} totalCount={count} pageSize={PAGE_SIZE} onPageChange={setPage} />
      </Spin>
    </Space>
  );
}
