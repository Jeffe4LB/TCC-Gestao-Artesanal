import { Button, Card, Checkbox, Form, Input, Select, Space } from "antd";
import {
  DEFAULT_PRODUCT_UNIT,
  PRODUCT_UNIT_OPTIONS,
  type ProductUnitCode,
} from "../../constants/unidades";
import type { Categoria, Fornecedor, Produto, TipoProduto } from "../../types/cadastro";

export type FormProduto = {
  sku: string;
  nome: string;
  descricao: string;
  categoria: number | "";
  fornecedor: number | "" | null;
  tipo_produto: TipoProduto;
  unidade: ProductUnitCode;
  preco_venda: string;
  custo_aquisicao: string;
  estoque_minimo: string;
  custo_unitario_display: string;
  ativo: boolean;
};

export type FormularioProdutoProps = {
  form: FormProduto;
  editing: Produto | null;
  saving: boolean;
  categories: Categoria[];
  suppliers: Fornecedor[];
  onFormChange: (updater: (prev: FormProduto) => FormProduto) => void;
  onSubmit: () => void;
  onCancel: () => void;
};

export function FormularioProduto({
  form,
  editing,
  saving,
  categories,
  suppliers,
  onFormChange,
  onSubmit,
  onCancel,
}: FormularioProdutoProps) {
  const setForm = (patch: Partial<FormProduto> | ((f: FormProduto) => FormProduto)) => {
    if (typeof patch === "function") {
      onFormChange(patch);
    } else {
      onFormChange((f) => ({ ...f, ...patch }));
    }
  };

  return (
    <Card
      size="small"
      title={editing ? "Editar produto" : "Novo produto"}
      extra={
        editing ? (
          <Button type="link" onClick={onCancel}>
            Cancelar
          </Button>
        ) : null
      }
    >
      <Form layout="vertical" onFinish={() => onSubmit()}>
        <Space wrap size="middle" style={{ width: "100%" }}>
          <Form.Item label="Código (SKU) *" required style={{ minWidth: 120, marginBottom: 0 }}>
            <Input
              value={form.sku}
              onChange={(e) => setForm({ sku: e.target.value })}
              disabled={!!editing}
            />
          </Form.Item>
          <Form.Item label="Nome *" required style={{ minWidth: 200, marginBottom: 0 }}>
            <Input value={form.nome} onChange={(e) => setForm({ nome: e.target.value })} />
          </Form.Item>
          <Form.Item label="Categoria *" required style={{ minWidth: 200, marginBottom: 0 }}>
            <Select
              placeholder="Selecione…"
              value={form.categoria === "" ? undefined : String(form.categoria)}
              onChange={(v) => setForm({ categoria: v ? Number(v) : "" })}
              options={categories.map((c) => ({ value: String(c.id), label: c.nome }))}
              style={{ width: "100%" }}
            />
          </Form.Item>
          <Form.Item label="Fornecedor (opc.)" style={{ minWidth: 200, marginBottom: 0 }}>
            <Select
              allowClear
              placeholder="—"
              value={
                form.fornecedor === "" || form.fornecedor === null
                  ? undefined
                  : String(form.fornecedor)
              }
              onChange={(v) => setForm({ fornecedor: v ? Number(v) : "" })}
              options={suppliers.map((s) => ({ value: String(s.id), label: s.nome }))}
              style={{ width: "100%" }}
            />
          </Form.Item>
          <Form.Item label="Tipo *" style={{ minWidth: 220, marginBottom: 0 }}>
            <Select
              value={form.tipo_produto}
              onChange={(v) =>
                setForm((f) => ({
                  ...f,
                  tipo_produto: v as TipoProduto,
                  custo_aquisicao: v === "fabricado" ? "0" : f.custo_aquisicao,
                }))
              }
              options={[
                { value: "comprado", label: "Comprado" },
                { value: "fabricado", label: "Produzido manualmente" },
              ]}
            />
          </Form.Item>
          <Form.Item label="Unidade *" required style={{ minWidth: 200, marginBottom: 0 }}>
            <Select<ProductUnitCode>
              value={form.unidade}
              onChange={(v) => setForm({ unidade: v })}
              options={PRODUCT_UNIT_OPTIONS}
              placeholder="Selecione…"
            />
          </Form.Item>
          <Form.Item
            label={
              form.tipo_produto === "fabricado"
                ? "Preço de venda (R$) *"
                : "Preço de venda (R$)"
            }
            required={form.tipo_produto === "fabricado"}
            style={{ minWidth: 140, marginBottom: 0 }}
          >
            <Input
              inputMode="decimal"
              value={form.preco_venda}
              onChange={(e) => setForm({ preco_venda: e.target.value })}
              placeholder={form.tipo_produto === "comprado" ? "0,00 (opcional)" : "0,00"}
            />
          </Form.Item>
          {form.tipo_produto === "comprado" ? (
            <Form.Item
              label="Custo de aquisição (R$ / unid.) *"
              required
              style={{ minWidth: 200, marginBottom: 0 }}
            >
              <Input
                inputMode="decimal"
                value={form.custo_aquisicao}
                onChange={(e) => setForm({ custo_aquisicao: e.target.value })}
                placeholder="0,00"
              />
            </Form.Item>
          ) : (
            <Form.Item label="Custo unitário (receita)" style={{ minWidth: 160, marginBottom: 0 }}>
              <Input value={form.custo_unitario_display || "0"} disabled />
            </Form.Item>
          )}
          <Form.Item label="Estoque mínimo" style={{ minWidth: 120, marginBottom: 0 }}>
            <Input
              value={form.estoque_minimo}
              onChange={(e) => setForm({ estoque_minimo: e.target.value })}
            />
          </Form.Item>
        </Space>
        <Form.Item label="Descrição">
          <Input.TextArea
            value={form.descricao}
            onChange={(e) => setForm({ descricao: e.target.value })}
            rows={2}
          />
        </Form.Item>
        <Checkbox checked={form.ativo} onChange={(e) => setForm({ ativo: e.target.checked })}>
          Ativo
        </Checkbox>
        <div style={{ marginTop: 12 }}>
          <Button type="primary" htmlType="submit" loading={saving}>
            Salvar
          </Button>
        </div>
      </Form>
    </Card>
  );
}

export const formProdutoVazio: FormProduto = {
  sku: "",
  nome: "",
  descricao: "",
  categoria: "",
  fornecedor: "",
  tipo_produto: "comprado",
  unidade: DEFAULT_PRODUCT_UNIT,
  preco_venda: "0",
  custo_aquisicao: "0",
  estoque_minimo: "0",
  custo_unitario_display: "",
  ativo: true,
};
