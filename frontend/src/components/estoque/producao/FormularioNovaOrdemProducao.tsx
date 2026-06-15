import {
  Button,
  Card,
  Form,
  Input,
  Select,
  Space,
  theme,
  Tooltip,
  Typography,
} from "antd";
import { DeleteOutlined, PlusOutlined } from "@ant-design/icons";
import { coerceProductUnitCode, type ProductUnitCode } from "../../../constants/unidades";
import type { Produto } from "../../../types/cadastro";
import { formatarBRL } from "../../../utils/previaCustoProducao";

export type LinhaFormOrdemProducao = {
  insumo: string;
  quantidade_consumida: string;
  quantidade_consumida_unidade: ProductUnitCode | "";
};

export type FormularioNovaOrdemProducaoProps = {
  productsMfg: Produto[];
  productsAll: Produto[];
  formProduto: string;
  onFormProdutoChange: (value: string) => void;
  formQty: string;
  onFormQtyChange: (value: string) => void;
  formQtyUnit: ProductUnitCode;
  onFormQtyUnitChange: (value: ProductUnitCode) => void;
  producedUnitOptions: { value: ProductUnitCode; label: string }[];
  formNotes: string;
  onFormNotesChange: (value: string) => void;
  formLines: LinhaFormOrdemProducao[];
  onAddLine: () => void;
  onRemoveLine: (index: number) => void;
  onUpdateLine: (index: number, patch: Partial<LinhaFormOrdemProducao>) => void;
  unitOptionsForComponent: (insumoId: string) => { value: ProductUnitCode; label: string }[];
  costPreview: {
    materialsTotal: number;
    hasValidLines: boolean;
  };
  finishedProduto: Produto | undefined;
  saving: boolean;
  onSubmit: () => void;
  onReset: () => void;
};

export function FormularioNovaOrdemProducao({
  productsMfg,
  productsAll,
  formProduto,
  onFormProdutoChange,
  formQty,
  onFormQtyChange,
  formQtyUnit,
  onFormQtyUnitChange,
  producedUnitOptions,
  formNotes,
  onFormNotesChange,
  formLines,
  onAddLine,
  onRemoveLine,
  onUpdateLine,
  unitOptionsForComponent,
  costPreview,
  finishedProduto,
  saving,
  onSubmit,
  onReset,
}: FormularioNovaOrdemProducaoProps) {
  const { token } = theme.useToken();

  return (
    <Card size="small" title="Nova ordem de produção">
      <Form layout="vertical" onFinish={() => onSubmit()}>
        <Form.Item label="Produto fabricado *" required>
          <Select
            placeholder="Selecione…"
            value={formProduto || undefined}
            onChange={(v) => onFormProdutoChange(v ?? "")}
            options={productsMfg.map((p) => ({
              value: String(p.id),
              label: `${p.sku} — ${p.nome}`,
            }))}
            showSearch
            optionFilterProp="label"
            style={{ maxWidth: 400 }}
          />
        </Form.Item>
        <Form.Item label="Quantidade produzida *" required>
          <Space wrap align="start">
            <Input
              inputMode="decimal"
              value={formQty}
              onChange={(e) => onFormQtyChange(e.target.value)}
              placeholder="> 0"
              style={{ width: 160 }}
            />
            <Select<ProductUnitCode>
              style={{ width: 200 }}
              value={formQtyUnit}
              onChange={(v) => onFormQtyUnitChange(v)}
              options={producedUnitOptions}
            />
          </Space>
        </Form.Item>
        {formProduto ? (
          <div
            style={{
              marginBottom: 16,
              padding: 12,
              borderRadius: token.borderRadiusLG,
              background: token.colorFillAlter,
              border: `1px solid ${token.colorBorderSecondary}`,
            }}
          >
            <Typography.Text strong style={{ display: "block" }}>
              Custo estimado
            </Typography.Text>
            <Space size={24} wrap align="start">
              <div>
                <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                  Total de insumos
                </Typography.Text>
                <Typography.Title level={4} style={{ margin: "4px 0 0" }}>
                  {formatarBRL(costPreview.materialsTotal)}
                </Typography.Title>
                {!costPreview.hasValidLines ? (
                  <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                    Preencha insumo e quantidade para somar.
                  </Typography.Text>
                ) : null}
              </div>
              {finishedProduto ? (
                <div>
                  <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                    Custo unitário na ficha do produto
                  </Typography.Text>
                  <Typography.Title level={5} style={{ margin: "4px 0 0" }}>
                    {formatarBRL(
                      Number(String(finishedProduto.custo_unitario).replace(",", ".")) || 0,
                    )}
                  </Typography.Title>
                  <Typography.Text type="secondary" style={{ fontSize: 11 }}>
                    Origem: {finishedProduto.origem_custo === "receita" ? "Receita" : "Cadastro"}
                  </Typography.Text>
                </div>
              ) : null}
            </Space>
          </div>
        ) : null}
        <Form.Item label="Observações">
          <Input value={formNotes} onChange={(e) => onFormNotesChange(e.target.value)} />
        </Form.Item>
        <Space direction="vertical" style={{ width: "100%" }} size="middle">
          <Space>
            <Typography.Text type="secondary">Consumo de insumos (totais nesta ordem)</Typography.Text>
            <Button type="dashed" icon={<PlusOutlined />} onClick={onAddLine}>
              Linha
            </Button>
          </Space>
          {formLines.map((row, idx) => (
            <Space key={idx} wrap style={{ width: "100%" }} align="start">
              <Form.Item label="Insumo" style={{ minWidth: 240, marginBottom: 0 }}>
                <Select
                  placeholder="Selecione…"
                  value={row.insumo || undefined}
                  onChange={(v) => {
                    const id = v ?? "";
                    const p = productsAll.find((x) => String(x.id) === id);
                    const defaultUnit: ProductUnitCode | "" = p
                      ? coerceProductUnitCode(p.unidade)
                      : "";
                    onUpdateLine(idx, {
                      insumo: id,
                      quantidade_consumida_unidade: defaultUnit,
                    });
                  }}
                  showSearch
                  optionFilterProp="label"
                  options={productsAll.map((p) => ({
                    value: String(p.id),
                    label: `${p.sku} — ${p.nome}`,
                  }))}
                  style={{ width: 280 }}
                />
              </Form.Item>
              <Form.Item label="Qtd consumida" style={{ width: 120, marginBottom: 0 }}>
                <Input
                  inputMode="decimal"
                  value={row.quantidade_consumida}
                  onChange={(e) => onUpdateLine(idx, { quantidade_consumida: e.target.value })}
                />
              </Form.Item>
              <Form.Item label="Unidade" style={{ width: 200, marginBottom: 0 }}>
                <Select<ProductUnitCode>
                  disabled={!row.insumo}
                  value={row.quantidade_consumida_unidade || undefined}
                  placeholder="Insumo…"
                  onChange={(v) => onUpdateLine(idx, { quantidade_consumida_unidade: v })}
                  options={unitOptionsForComponent(row.insumo)}
                />
              </Form.Item>
              <Tooltip title="Remover linha">
                <Button
                  danger
                  type="text"
                  icon={<DeleteOutlined />}
                  aria-label="Remover linha"
                  onClick={() => onRemoveLine(idx)}
                  disabled={formLines.length <= 1}
                  style={{ marginTop: 30 }}
                />
              </Tooltip>
            </Space>
          ))}
        </Space>
        <Space style={{ marginTop: 16 }}>
          <Button type="primary" htmlType="submit" loading={saving}>
            Registrar produção
          </Button>
          <Button onClick={onReset}>Limpar</Button>
        </Space>
      </Form>
    </Card>
  );
}
