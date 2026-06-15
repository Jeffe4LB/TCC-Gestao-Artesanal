import { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Button,
  Card,
  DatePicker,
  Form,
  Input,
  Select,
  Space,
  Typography,
} from "antd";
import { MinusCircleOutlined, PlusOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import { useNavigate } from "react-router-dom";
import { listarTodosFornecedores, listarTodosProdutos } from "../../api/cadastro";
import { criarEntradaCompra } from "../../api/estoque";
import {
  coerceProductUnitCode,
  compatibleUnitsForProduct,
  DEFAULT_PRODUCT_UNIT,
  PRODUCT_UNIT_OPTIONS,
} from "../../constants/unidades";
import type { ProductUnitCode } from "../../constants/unidades";
import type { Fornecedor, Produto } from "../../types/cadastro";
import type { RespostaEntradaCompra } from "../../types/estoque";
import { convertQuantitySameCategoria } from "../../utils/conversaoUnidade";

type LineForm = {
  produto: string;
  quantidade: string;
  unidade: ProductUnitCode;
  custo_unitario: string;
};

const emptyLine = (): LineForm => ({
  produto: "",
  quantidade: "1",
  unidade: DEFAULT_PRODUCT_UNIT,
  custo_unitario: "",
});

function parseDecimal(raw: string | undefined): number | null {
  const t = (raw ?? "").trim().replace(",", ".");
  if (t === "") return null;
  const n = Number(t);
  if (!Number.isFinite(n)) return null;
  return n;
}

function lineSubtotalCompra(
  q: string,
  unit: ProductUnitCode,
  produto: Produto | undefined,
  custoStr: string,
): number {
  if (!produto) return 0;
  const qty = parseDecimal(q);
  const custo = parseDecimal(custoStr);
  if (qty === null || custo === null || qty <= 0 || custo <= 0) return 0;
  const catalogUnit = coerceProductUnitCode(produto.unidade);
  const qtyCatalog = convertQuantitySameCategoria(qty, unit, catalogUnit);
  if (qtyCatalog === null) return 0;
  return Math.round(qtyCatalog * custo * 100) / 100;
}

export function EntradaCompraPage() {
  const navigate = useNavigate();
  const [suppliers, setFornecedores] = useState<Fornecedor[]>([]);
  const [products, setProdutos] = useState<Produto[]>([]);
  const [fornecedor, setFornecedor] = useState<string>("");
  const [descricao, setDescricao] = useState("");
  const [vencimento, setVencimento] = useState("");
  const [observacoes, setObservacoes] = useState("");
  const [linhas, setLinhas] = useState<LineForm[]>([emptyLine()]);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [ok, setOk] = useState<RespostaEntradaCompra | null>(null);

  const produtosCompra = useMemo(
    () => products.filter((p) => p.tipo_produto === "comprado"),
    [products],
  );

  useEffect(() => {
    void listarTodosFornecedores().then(setFornecedores).catch(() => {});
    void listarTodosProdutos({ ativo: true }).then(setProdutos).catch(() => {});
  }, []);

  const documentTotal = useMemo(
    () =>
      linhas.reduce((s, ln) => {
        const p = produtosCompra.find((x) => String(x.id) === ln.produto);
        const custo =
          ln.custo_unitario.trim() !== ""
            ? ln.custo_unitario
            : p?.custo_aquisicao ?? "0";
        return s + lineSubtotalCompra(ln.quantidade, ln.unidade, p, custo);
      }, 0),
    [linhas, produtosCompra],
  );

  const updateLine = (idx: number, patch: Partial<LineForm>) => {
    setLinhas((rows) => {
      const next = [...rows];
      const cur = { ...next[idx], ...patch };
      if (patch.produto != null) {
        const p = produtosCompra.find((x) => String(x.id) === cur.produto);
        if (p) {
          const u = coerceProductUnitCode(p.unidade);
          cur.unidade = compatibleUnitsForProduct(u).includes(cur.unidade)
            ? cur.unidade
            : compatibleUnitsForProduct(u)[0] ?? DEFAULT_PRODUCT_UNIT;
          if (!cur.custo_unitario.trim()) {
            cur.custo_unitario = p.custo_aquisicao ?? "0";
          }
        }
      }
      next[idx] = cur;
      return next;
    });
  };

  const submit = async () => {
    if (!descricao.trim() || !vencimento) {
      setErr("Preencha descrição e vencimento da conta a pagar.");
      return;
    }
    const payloadLines = linhas
      .filter((ln) => ln.produto.trim())
      .map((ln) => {
        const p = produtosCompra.find((x) => String(x.id) === ln.produto);
        const custo =
          ln.custo_unitario.trim() !== ""
            ? ln.custo_unitario.trim()
            : p?.custo_aquisicao ?? "";
        return {
          produto: Number(ln.produto),
          quantidade: ln.quantidade.trim(),
          unidade: ln.unidade,
          custo_unitario: custo,
        };
      });
    if (!payloadLines.length) {
      setErr("Inclua ao menos uma linha com produto comprado.");
      return;
    }
    for (let i = 0; i < payloadLines.length; i++) {
      const ln = payloadLines[i];
      const q = parseDecimal(ln.quantidade);
      const c = parseDecimal(String(ln.custo_unitario));
      if (q === null || q <= 0) {
        setErr(`Linha ${i + 1}: quantidade deve ser maior que zero.`);
        return;
      }
      if (c === null || c <= 0) {
        setErr(`Linha ${i + 1}: informe custo unitário (cadastro ou na linha).`);
        return;
      }
    }

    setSaving(true);
    setErr(null);
    setOk(null);
    try {
      const res = await criarEntradaCompra({
        fornecedor: fornecedor === "" ? null : Number(fornecedor),
        descricao: descricao.trim(),
        vencimento,
        observacoes: observacoes.trim(),
        linhas: payloadLines,
      });
      setOk(res);
      setLinhas([emptyLine()]);
      setDescricao("");
      setVencimento("");
      setObservacoes("");
      setFornecedor("");
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Erro ao registrar entrada");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Typography.Title level={3} style={{ margin: 0 }}>
        Entrada de compra
      </Typography.Title>

      <Card size="small" title="Dados da compra">
        <Form layout="vertical" onFinish={() => void submit()}>
          <Space wrap size="middle" style={{ width: "100%" }}>
            <Form.Item label="Fornecedor" style={{ minWidth: 240, marginBottom: 0 }}>
              <Select
                allowClear
                placeholder="—"
                value={fornecedor || undefined}
                onChange={(v) => setFornecedor(v ?? "")}
                showSearch
                optionFilterProp="label"
                options={suppliers.map((s) => ({ value: String(s.id), label: s.nome }))}
                style={{ width: 260 }}
              />
            </Form.Item>
            <Form.Item label="Descrição da conta *" required style={{ minWidth: 260, flex: 1, marginBottom: 0 }}>
              <Input value={descricao} onChange={(e) => setDescricao(e.target.value)} />
            </Form.Item>
            <Form.Item label="Vencimento *" required style={{ marginBottom: 0 }}>
              <DatePicker
                format="YYYY-MM-DD"
                value={vencimento ? dayjs(vencimento) : null}
                onChange={(_, s) => setVencimento(typeof s === "string" ? s : "")}
              />
            </Form.Item>
          </Space>

          <Typography.Text strong style={{ display: "block", marginTop: 16 }}>
            Itens
          </Typography.Text>
          <Space direction="vertical" style={{ width: "100%" }} size="small">
            {linhas.map((ln, idx) => {
              const p = produtosCompra.find((x) => String(x.id) === ln.produto);
              const unitOpts = p
                ? PRODUCT_UNIT_OPTIONS.filter((o) =>
                    compatibleUnitsForProduct(coerceProductUnitCode(p.unidade)).includes(o.value),
                  )
                : PRODUCT_UNIT_OPTIONS;
              const custo =
                ln.custo_unitario.trim() !== ""
                  ? ln.custo_unitario
                  : p?.custo_aquisicao ?? "0";
              const sub = lineSubtotalCompra(ln.quantidade, ln.unidade, p, custo);
              return (
                <Space key={idx} wrap style={{ width: "100%", alignItems: "flex-start" }}>
                  <Select
                    placeholder="Produto comprado *"
                    value={ln.produto || undefined}
                    onChange={(v) => updateLine(idx, { produto: v ?? "" })}
                    showSearch
                    optionFilterProp="label"
                    style={{ minWidth: 240, flex: 1 }}
                    options={produtosCompra.map((x) => ({
                      value: String(x.id),
                      label: `${x.sku} — ${x.nome}`,
                    }))}
                  />
                  <Input
                    style={{ width: 88 }}
                    inputMode="decimal"
                    placeholder="Qtd"
                    value={ln.quantidade}
                    onChange={(e) => updateLine(idx, { quantidade: e.target.value })}
                  />
                  <Select<ProductUnitCode>
                    style={{ width: 120 }}
                    value={ln.unidade}
                    onChange={(v) => updateLine(idx, { unidade: v })}
                    options={unitOpts}
                  />
                  <Input
                    style={{ width: 110 }}
                    inputMode="decimal"
                    placeholder="Custo un."
                    value={ln.custo_unitario}
                    onChange={(e) => updateLine(idx, { custo_unitario: e.target.value })}
                    title="Por unidade de cadastro do produto"
                  />
                  <Typography.Text type="secondary" style={{ minWidth: 80 }}>
                    = R$ {sub.toFixed(2)}
                  </Typography.Text>
                  <Button
                    type="text"
                    danger
                    icon={<MinusCircleOutlined />}
                    onClick={() =>
                      setLinhas((rows) =>
                        rows.length > 1 ? rows.filter((_, i) => i !== idx) : rows,
                      )
                    }
                    disabled={linhas.length <= 1}
                  />
                </Space>
              );
            })}
            <Button
              type="dashed"
              icon={<PlusOutlined />}
              onClick={() => setLinhas((rows) => [...rows, emptyLine()])}
            >
              Adicionar produto
            </Button>
          </Space>

          <Typography.Text style={{ display: "block", marginTop: 8 }}>
            Total estimado da conta: <strong>R$ {documentTotal.toFixed(2)}</strong>
          </Typography.Text>

          <Form.Item label="Observações" style={{ marginTop: 8 }}>
            <Input.TextArea
              value={observacoes}
              onChange={(e) => setObservacoes(e.target.value)}
              rows={2}
            />
          </Form.Item>

          <Button type="primary" htmlType="submit" loading={saving}>
            Registrar entrada e gerar conta a pagar
          </Button>
        </Form>
      </Card>

      {err ? <Alert type="error" message={err} showIcon /> : null}

      {ok ? (
        <Alert
          type="success"
          showIcon
          message={`Entrada registrada. Conta a pagar #${ok.conta_pagar.id} — R$ ${ok.conta_pagar.valor}`}
          action={
            <Button size="small" onClick={() => navigate("/app/financeiro/pagar")}>
              Ver contas a pagar
            </Button>
          }
        />
      ) : null}
    </Space>
  );
}
