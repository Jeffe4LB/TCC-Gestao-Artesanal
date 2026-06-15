import { Link } from "react-router-dom";
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
import { BarraPaginacao } from "../../components/BarraPaginacao";
import { listarTodosProdutos } from "../../api/cadastro";
import { criarMovimentacaoEstoque, listarMovimentacoesEstoque } from "../../api/estoque";
import {
  baseUnitForProductUnit,
  coerceProductUnitCode,
  compatibleUnitsForProduct,
  PRODUCT_UNIT_OPTIONS,
} from "../../constants/unidades";
import type { Produto } from "../../types/cadastro";
import type { ProductUnitCode } from "../../constants/unidades";
import type { MovimentacaoEstoque } from "../../types/estoque";
import type { ColumnsType } from "antd/es/table";
import {
  OPCOES_FILTRO_TIPO_MOVIMENTACAO,
  rotuloTipoMovimentacao,
} from "../../constants/tiposMovimentacaoEstoque";
import {
  formatBalanceDisplay,
  formatQuantityWithUnit,
} from "../../utils/exibicaoQuantidade";

const PAGE_SIZE = 20;

export function MovimentacoesEstoquePage() {
  const [list, setList] = useState<MovimentacaoEstoque[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [produtoId, setProdutoId] = useState<string>("");
  const [tipoMovimentacao, setMovementType] = useState<string>("");
  const [products, setProdutos] = useState<Produto[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const [formTipo] = useState<"ajuste">("ajuste");
  const [formProduto, setFormProduto] = useState<string>("");
  const [formUnit, setFormUnit] = useState<ProductUnitCode>("UN");
  const [formQty, setFormQty] = useState("");
  const [formNotes, setFormNotes] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    void listarTodosProdutos({ ativo: true }).then(setProdutos).catch(() => {});
  }, []);

  useEffect(() => {
    const p = products.find((x) => String(x.id) === formProduto);
    if (p) {
      const u = coerceProductUnitCode(p.unidade);
      setFormUnit(baseUnitForProductUnit(u));
    }
  }, [formProduto, products]);

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const data = await listarMovimentacoesEstoque({
        page,
        search: search || undefined,
        produto: produtoId || undefined,
        tipo_movimentacao: tipoMovimentacao || undefined,
        ordering: "-criado_em",
      });
      setList(data.resultados);
      setCount(data.total);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao listar");
    } finally {
      setLoading(false);
    }
  }, [page, search, produtoId, tipoMovimentacao]);

  useEffect(() => {
    void load();
  }, [load]);

  const submitMovement = async () => {
    if (!formProduto) {
      setErr("Selecione o produto.");
      return;
    }
    const qtyNum = Number(String(formQty).trim().replace(",", "."));
    if (!Number.isFinite(qtyNum)) {
      setErr("Quantidade inválida.");
      return;
    }
    if (qtyNum === 0) {
      setErr("Ajuste não pode ser zero (use valor negativo para baixa).");
      return;
    }
    setSaving(true);
    setErr(null);
    try {
      await criarMovimentacaoEstoque({
        tipo_movimentacao: formTipo,
        produto: Number(formProduto),
        quantidade: formQty.trim(),
        unidade: formUnit,
        observacoes: formNotes.trim() || undefined,
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
    const p = products.find((x) => String(x.id) === formProduto);
    if (!p) return PRODUCT_UNIT_OPTIONS;
    const codes = compatibleUnitsForProduct(coerceProductUnitCode(p.unidade));
    return PRODUCT_UNIT_OPTIONS.filter((o) => codes.includes(o.value));
  }, [formProduto, products]);

  const columns: ColumnsType<MovimentacaoEstoque> = useMemo(
    () => [
      {
        title: "Data",
        dataIndex: "criado_em",
        key: "criado_em",
        render: (v: string) => new Date(v).toLocaleString(),
      },
      { title: "Código (SKU)", dataIndex: "codigo_produto", key: "codigo_produto" },
      {
        title: "Δ (base)",
        key: "qd",
        render: (_: unknown, r: MovimentacaoEstoque) =>
          formatBalanceDisplay(r.delta_quantidade, r.unidade_base),
      },
      {
        title: "Informado",
        key: "qin",
        render: (_: unknown, r: MovimentacaoEstoque) =>
          r.quantidade_informada != null && r.unidade_informada
            ? formatQuantityWithUnit(r.quantidade_informada, r.unidade_informada)
            : "—",
      },
      {
        title: "Tipo",
        dataIndex: "tipo_movimentacao",
        key: "tipo_movimentacao",
        render: (c: string) => rotuloTipoMovimentacao(c),
      },
      {
        title: "Responsável",
        dataIndex: "criado_por_nome",
        key: "criado_por_nome",
        width: 120,
        render: (v: string | null | undefined) => v ?? "—",
      },
      {
        title: "Conta pagar",
        dataIndex: "conta_pagar",
        key: "conta_pagar",
        width: 96,
        render: (v: number | null | undefined) =>
          v != null ? (
            <Link to="/app/financeiro/pagar">#{v}</Link>
          ) : (
            "—"
          ),
      },
      { title: "Obs.", dataIndex: "observacoes", key: "observacoes", render: (v) => v || "—" },
    ],
    [],
  );

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Typography.Title level={3} style={{ margin: 0 }}>
        Movimentos
      </Typography.Title>

      <Card size="small" title="Novo ajuste manual">
        <Form layout="vertical" onFinish={() => void submitMovement()}>
          <Space wrap size="middle" style={{ width: "100%" }}>
            <Form.Item label="Produto *" required style={{ minWidth: 260, marginBottom: 0, flex: 1 }}>
              <Select
                placeholder="Selecione…"
                value={formProduto || undefined}
                onChange={(v) => setFormProduto(v ?? "")}
                showSearch
                optionFilterProp="label"
                options={products.map((p) => ({
                  value: String(p.id),
                  label: `${p.sku} — ${p.nome}`,
                }))}
                style={{ width: "100%" }}
              />
            </Form.Item>
            <Form.Item label="Quantidade *" required style={{ minWidth: 140, marginBottom: 0 }}>
              <Input
                inputMode="decimal"
                value={formQty}
                onChange={(e) => setFormQty(e.target.value)}
                placeholder="ex.: 10 ou -2"
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
            placeholder="Buscar código ou observação"
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
            value={produtoId || undefined}
            onChange={(v) => {
              setProdutoId(v ?? "");
              setPage(1);
            }}
            allowClear
            showSearch
            optionFilterProp="label"
            style={{ width: 280 }}
            options={products.map((p) => ({
              value: String(p.id),
              label: `${p.sku} — ${p.nome}`,
            }))}
          />
          <Select
            placeholder="Tipo"
            value={tipoMovimentacao || undefined}
            onChange={(v) => {
              setMovementType(v ?? "");
              setPage(1);
            }}
            allowClear
            style={{ width: 220 }}
            options={[...OPCOES_FILTRO_TIPO_MOVIMENTACAO]}
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
        <Table<MovimentacaoEstoque> rowKey="id" columns={columns} dataSource={list} pagination={false} />
        <BarraPaginacao page={page} totalCount={count} pageSize={PAGE_SIZE} onPageChange={setPage} />
      </Spin>
    </Space>
  );
}
