export type FormatoExportacao = "csv" | "pdf" | "xlsx";

export const FORMATOS_EXPORTACAO: FormatoExportacao[] = ["csv", "pdf", "xlsx"];

export const EXTENSAO_POR_FORMATO: Record<FormatoExportacao, string> = {
  csv: "csv",
  pdf: "pdf",
  xlsx: "xlsx",
};

export const ROTULO_FORMATO: Record<FormatoExportacao, string> = {
  csv: "CSV",
  pdf: "PDF",
  xlsx: "Excel (XLSX)",
};

export type LinhaPosicaoEstoque = {
  sku: string;
  nome: string;
  categoria: string;
  quantidade: string;
  unidade_base?: string;
  estoque_minimo: string;
  abaixo_minimo: boolean;
};


export type ResumoPosicaoEstoque = {
  total_skus: number;
  valor_estoque: string;
};

export type RelatorioPosicaoEstoque = {
  total: number;
  resumo?: ResumoPosicaoEstoque;
  resultados: LinhaPosicaoEstoque[];
};


export type LinhaMovimentacaoEstoqueRelatorio = {
  id: number;
  criado_em: string;
  sku: string;
  nome_produto: string;
  delta_quantidade: string;
  unidade_base?: string;
  tipo_movimentacao: string;
  criado_por_nome?: string | null;
  observacoes: string;
};


export type ResumoMovimentacoesEstoque = {
  total_no_periodo: number;
  contagem_por_tipo: Record<string, number>;
  limite_previa: number;
  truncado: boolean;
};

export type RelatorioMovimentacoesEstoque = {
  de: string;
  ate: string;
  total: number;
  resumo?: ResumoMovimentacoesEstoque;
  resultados: LinhaMovimentacaoEstoqueRelatorio[];
};


export type LinhaEstoqueAbaixoMinimo = {
  sku: string;
  nome: string;
  estoque_minimo: string;
  quantidade_atual: string;
  unidade_base?: string;
  gap: string;
};


export type ResumoEstoqueAbaixoMinimo = {
  itens_criticos: number;
};

export type RelatorioEstoqueAbaixoMinimo = {
  total: number;
  resumo?: ResumoEstoqueAbaixoMinimo;
  resultados: LinhaEstoqueAbaixoMinimo[];
};


export type LinhaContaPagarAberta = {
  id: number;
  descricao: string;
  valor: string;
  vencimento: string;
  fornecedor: string | null;
};


export type LinhaContaReceberAberta = {
  id: number;
  descricao: string;
  valor: string;
  vencimento: string;
  cliente: string | null;
};


export type RelatorioFinanceiroEmAberto = {
  resumo: {
    contagem_pagar: number;
    total_pagar: string;
    contagem_receber: number;
    total_receber: string;
    saldo_liquido: string;
  };
  contas_pagar: LinhaContaPagarAberta[];
  contas_receber: LinhaContaReceberAberta[];
};


export type RelatorioFluxoCaixa = {
  de: string;
  ate: string;
  entradas: string;
  saidas: string;
  liquido: string;
};


export type FaixaEnvelhecimento = {
  quantidade: number;
  total: string;
};


export type RelatorioEnvelhecimentoFinanceiro = {
  hoje: string;
  pagar: Record<string, FaixaEnvelhecimento>;
  receber: Record<string, FaixaEnvelhecimento>;
};


export type LinhaReceitaPorProduto = {
  id_produto: number;
  sku: string;
  nome: string;
  categoria: string;
  quantidade: string;
  faturamento_total: string;
  custo_total: string;
  lucro: string;
  margem_percentual: string;
};


export type ResumoReceitaPorProduto = {
  faturamento_total: string;
  custo_total: string;
  lucro_total: string;
  margem_percentual: string;
};

export type RelatorioReceitaPorProduto = {
  de: string;
  ate: string;
  total: number;
  resumo?: ResumoReceitaPorProduto;
  resultados: LinhaReceitaPorProduto[];
};


export type PontoFluxoMensal = {
  /** Primeiro dia do mês em ISO (estável para ordenação). Ex.: `2026-06-01`. */
  mes: string;
  /** Rótulo legível em pt-BR, ex.: `jun/2026`. */
  mes_rotulo: string;
  entradas: string;
  saidas: string;
  liquido: string;
};

export type RelatorioFluxoMensal = {
  meses: number;
  resultados: PontoFluxoMensal[];
};


export type LinhaEstoquePorCategoria = {
  categoria: string;
  total_skus: number;
  quantidade_total: string;
  valor_estoque: string;
};

export type RelatorioEstoquePorCategoria = {
  total_categorias: number;
  valor_total: string;
  resultados: LinhaEstoquePorCategoria[];
};

