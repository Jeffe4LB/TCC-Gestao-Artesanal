import type { ProductUnitCode } from "../constants/unidades";

export type { ProductUnitCode };

export type PaginatedResponse<T> = {
  total: number;
  proximo: string | null;
  anterior: string | null;
  resultados: T[];
};

export type Categoria = {
  id: number;
  nome: string;
  criado_em: string;
  atualizado_em: string;
};

export type Fornecedor = {
  id: number;
  nome: string;
  razao_social: string;
  documento: string;
  telefone: string;
  email: string;
  observacoes: string;
  ativo: boolean;
  criado_em: string;
  atualizado_em: string;
};

export type Cliente = {
  id: number;
  nome: string;
  documento: string;
  telefone: string;
  email: string;
  endereco: string;
  ativo: boolean;
  criado_em: string;
  atualizado_em: string;
};

export type TipoProduto = "comprado" | "fabricado";

export type OrigemCustoProduto = "aquisicao" | "receita";

export type Produto = {
  id: number;
  sku: string;
  nome: string;
  descricao: string;
  categoria: number;
  nome_categoria: string;
  fornecedor: number | null;
  nome_fornecedor: string | null;
  tipo_produto: TipoProduto;
  unidade: ProductUnitCode;
  /** Catálogo: obrigatório > 0 só para `fabricado`; `comprado` pode ser `"0"` (sem venda direta). */
  preco_venda: string;
  custo_aquisicao: string;
  custo_unitario: string;
  origem_custo: OrigemCustoProduto;
  estoque_minimo: string;
  ativo: boolean;
  criado_em: string;
  atualizado_em: string;
};
