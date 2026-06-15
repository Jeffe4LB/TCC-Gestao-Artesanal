import { Link } from "react-router-dom";
import {
  Button,
  Card,
  Col,
  DatePicker,
  Form,
  Input,
  Row,
  Select,
  Space,
  Tooltip,
  Typography,
} from "antd";
import { MinusCircleOutlined, PlusOutlined, QuestionCircleOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import {
  coerceProductUnitCode,
  compatibleUnitsForProduct,
  PRODUCT_UNIT_OPTIONS,
  type ProductUnitCode,
} from "../../../constants/unidades";
import type { Cliente, Produto } from "../../../types/cadastro";
import type { ContaReceber, SituacaoReceber } from "../../../types/financeiro";
import { todayLocal } from "../../../utils/data";
import { FORM_ITEM_DATA, precoCatalogoParaLinha, totalLinha } from "./helpers";
import type { FormContaReceber, LinhaFormContaReceber } from "./types";

const GRID_LINHA_ITENS = {
  display: "grid",
  gridTemplateColumns: "minmax(200px, 1fr) 88px 120px 168px 88px 100px 32px",
  gap: 8,
  width: "100%",
  alignItems: "start",
} as const;

const LINK_PRECO_CATALOGO: React.CSSProperties = {
  display: "block",
  marginTop: 6,
  fontSize: 13,
  lineHeight: 1.45,
  whiteSpace: "normal",
  wordBreak: "break-word",
};

type RotuloColunaProps = {
  children: React.ReactNode;
  required?: boolean;
  tooltip?: string;
};

function RotuloColuna({ children, required, tooltip }: RotuloColunaProps) {
  return (
    <label
      style={{
        display: "block",
        fontSize: 14,
        lineHeight: "22px",
        marginBottom: 0,
        color: "rgba(0, 0, 0, 0.88)",
        whiteSpace: "nowrap",
      }}
    >
      {required ? (
        <span style={{ color: "#ff4d4f", marginInlineEnd: 4, fontFamily: "SimSun, sans-serif" }}>
          *
        </span>
      ) : null}
      {children}
      {tooltip ? (
        <Tooltip title={tooltip}>
          <QuestionCircleOutlined
            style={{ marginInlineStart: 4, color: "rgba(0, 0, 0, 0.45)", fontSize: 12 }}
          />
        </Tooltip>
      ) : null}
    </label>
  );
}

export type FormularioContaReceberProps = {
  form: FormContaReceber;
  editing: ContaReceber | null;
  saving: boolean;
  customers: Cliente[];
  products: Produto[];
  linesTotal: number;
  onFormChange: (updater: (prev: FormContaReceber) => FormContaReceber) => void;
  onSubmit: () => void;
  onCancel: () => void;
  onUpdateLine: (idx: number, patch: Partial<LinhaFormContaReceber>) => void;
  onAddLine: () => void;
  onRemoveLine: (idx: number) => void;
  onAplicarPrecoCatalogo: (idx: number) => void;
};

export function FormularioContaReceber({
  form,
  editing,
  saving,
  customers,
  products,
  linesTotal,
  onFormChange,
  onSubmit,
  onCancel,
  onUpdateLine,
  onAddLine,
  onRemoveLine,
  onAplicarPrecoCatalogo,
}: FormularioContaReceberProps) {
  const setForm = (patch: Partial<FormContaReceber> | ((f: FormContaReceber) => FormContaReceber)) => {
    if (typeof patch === "function") {
      onFormChange(patch);
    } else {
      onFormChange((f) => ({ ...f, ...patch }));
    }
  };

  return (
    <Card
      size="small"
      title={editing ? "Editar lançamento" : "Novo lançamento"}
      extra={
        <Space size="small">
          {!editing ? (
            <Link to="/app/financeiro/documentos?novo=receber">
              <Button type="default" size="small">
                Parcelamento
              </Button>
            </Link>
          ) : null}
          {editing || form.descricao ? (
            <Button type="link" size="small" onClick={onCancel}>
              Cancelar
            </Button>
          ) : null}
        </Space>
      }
    >
      <Form layout="vertical" onFinish={() => onSubmit()}>
        <Row gutter={[16, 8]}>
          <Col xs={24} lg={10}>
            <Form.Item label="Cliente">
              <Select
                allowClear
                placeholder="—"
                value={form.cliente || undefined}
                onChange={(v) => setForm({ cliente: v ?? "" })}
                options={customers.map((c) => ({ value: String(c.id), label: c.nome }))}
                showSearch
                optionFilterProp="label"
                style={{ width: "100%" }}
              />
            </Form.Item>
          </Col>
          <Col xs={24} lg={14}>
            <Form.Item label="Descrição" required>
              <Input
                value={form.descricao}
                onChange={(e) => setForm({ descricao: e.target.value })}
              />
            </Form.Item>
          </Col>
        </Row>
        <Row gutter={[16, 8]}>
          <Col xs={24} sm={12} md={6}>
            <Form.Item label="Emissão" required style={FORM_ITEM_DATA}>
              <DatePicker
                format="YYYY-MM-DD"
                style={{ width: "100%", minWidth: 140 }}
                value={form.data_emissao ? dayjs(form.data_emissao) : null}
                onChange={(_, s) =>
                  setForm({ data_emissao: typeof s === "string" ? s : "" })
                }
              />
            </Form.Item>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Form.Item label="Vencimento" required style={FORM_ITEM_DATA}>
              <DatePicker
                format="YYYY-MM-DD"
                style={{ width: "100%", minWidth: 140 }}
                value={form.vencimento ? dayjs(form.vencimento) : null}
                onChange={(_, s) => setForm({ vencimento: typeof s === "string" ? s : "" })}
              />
            </Form.Item>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Form.Item label="Status" style={FORM_ITEM_DATA}>
              <Select
                style={{ width: "100%", minWidth: 140 }}
                value={form.situacao}
                onChange={(status) => {
                  const s = status as SituacaoReceber;
                  setForm((f) => ({
                    ...f,
                    situacao: s,
                    recebido_em: s === "recebido" && !f.recebido_em ? todayLocal() : f.recebido_em,
                  }));
                }}
                options={[
                  { value: "aberto", label: "Em aberto" },
                  { value: "recebido", label: "Recebido" },
                  { value: "cancelado", label: "Cancelado" },
                ]}
              />
            </Form.Item>
          </Col>
          {form.situacao === "recebido" ? (
            <Col xs={24} sm={12} md={6}>
              <Form.Item label="Recebido em" required style={FORM_ITEM_DATA}>
                <DatePicker
                  format="YYYY-MM-DD"
                  style={{ width: "100%", minWidth: 140 }}
                  value={form.recebido_em ? dayjs(form.recebido_em) : null}
                  onChange={(_, s) =>
                    setForm({ recebido_em: typeof s === "string" ? s : "" })
                  }
                />
              </Form.Item>
            </Col>
          ) : null}
        </Row>

        <Typography.Text strong style={{ display: "block", marginTop: 12 }}>
          Itens (linhas)
        </Typography.Text>
        <div style={{ overflowX: "auto", marginTop: 8 }}>
          <div style={{ minWidth: 818 }}>
            <div style={{ ...GRID_LINHA_ITENS, marginBottom: 8 }}>
              <RotuloColuna required>Produto</RotuloColuna>
              <RotuloColuna required>Quantidade</RotuloColuna>
              <RotuloColuna>Unidade</RotuloColuna>
              <RotuloColuna
                required
                tooltip="Valor por unidade informada; pode vir do preço de venda do cadastro"
              >
                Preço unit.
              </RotuloColuna>
              <RotuloColuna tooltip="Valor em reais descontado nesta linha (opcional)">
                Desconto
              </RotuloColuna>
              <RotuloColuna>Total</RotuloColuna>
              <span aria-hidden />
            </div>
            <Space direction="vertical" style={{ width: "100%" }} size={12}>
              {form.linhas.map((ln, idx) => {
                const p = products.find((x) => String(x.id) === ln.produto);
                const unitOpts = p
                  ? PRODUCT_UNIT_OPTIONS.filter((o) =>
                      compatibleUnitsForProduct(coerceProductUnitCode(p.unidade)).includes(o.value),
                    )
                  : PRODUCT_UNIT_OPTIONS;
                const sub = totalLinha(ln.quantidade, ln.preco_unitario, ln.desconto);
                const precoCatalogo = p ? precoCatalogoParaLinha(p) : null;
                return (
                  <div key={idx} style={GRID_LINHA_ITENS}>
                    <Select
                      placeholder="Selecione…"
                      value={ln.produto || undefined}
                      onChange={(v) => onUpdateLine(idx, { produto: v ?? "" })}
                      showSearch
                      optionFilterProp="label"
                      style={{ width: "100%" }}
                      options={products.map((x) => ({
                        value: String(x.id),
                        label: `${x.sku} — ${x.nome}`,
                      }))}
                    />
                    <Input
                      inputMode="decimal"
                      placeholder="1"
                      value={ln.quantidade}
                      onChange={(e) => onUpdateLine(idx, { quantidade: e.target.value })}
                    />
                    <Select<ProductUnitCode>
                      value={ln.unidade}
                      onChange={(v) => onUpdateLine(idx, { unidade: v })}
                      options={unitOpts}
                    />
                    <div>
                      <Input
                        style={{ width: "100%" }}
                        inputMode="decimal"
                        placeholder={precoCatalogo ? "Ex.: 25,00" : "Informe o valor"}
                        value={ln.preco_unitario}
                        onChange={(e) => onUpdateLine(idx, { preco_unitario: e.target.value })}
                        aria-label="Preço unitário"
                      />
                      {precoCatalogo ? (
                        <Typography.Link
                          onClick={() => onAplicarPrecoCatalogo(idx)}
                          style={LINK_PRECO_CATALOGO}
                        >
                          Usar preço do cadastro
                        </Typography.Link>
                      ) : (
                        <Typography.Text
                          type="secondary"
                          style={{ ...LINK_PRECO_CATALOGO, fontSize: 12 }}
                        >
                          Sem preço no cadastro
                        </Typography.Text>
                      )}
                    </div>
                    <Input
                      inputMode="decimal"
                      placeholder="0,00"
                      value={ln.desconto}
                      onChange={(e) => onUpdateLine(idx, { desconto: e.target.value })}
                      aria-label="Desconto"
                    />
                    <Typography.Text
                      type="secondary"
                      style={{ display: "block", lineHeight: "32px", whiteSpace: "nowrap" }}
                    >
                      = R$ {sub.toFixed(2)}
                    </Typography.Text>
                    <Button
                      type="text"
                      danger
                      icon={<MinusCircleOutlined />}
                      style={{ marginTop: 0 }}
                      onClick={() => onRemoveLine(idx)}
                      disabled={form.linhas.length <= 1}
                    />
                  </div>
                );
              })}
            </Space>
          </div>
        </div>
        <Button
          type="dashed"
          icon={<PlusOutlined />}
          onClick={onAddLine}
          style={{ marginTop: 12 }}
        >
          Adicionar linha
        </Button>

        <Typography.Text style={{ display: "block", marginTop: 8 }}>
          Total: <strong>R$ {linesTotal.toFixed(2)}</strong> 
        </Typography.Text>

        <Form.Item label="Observações" style={{ marginTop: 8 }}>
          <Input.TextArea
            value={form.observacoes}
            onChange={(e) => setForm({ observacoes: e.target.value })}
            rows={2}
          />
        </Form.Item>
        <Button type="primary" htmlType="submit" loading={saving}>
          {editing ? "Salvar" : "Criar"}
        </Button>
      </Form>
    </Card>
  );
}
