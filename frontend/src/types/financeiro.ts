import type { ProductUnitCode } from "../constants/unidades";

export type SituacaoPagar = "aberto" | "parcial" | "pago" | "cancelado";
export type SituacaoReceber = "aberto" | "parcial" | "recebido" | "cancelado";

export type TipoDocumentoFinanceiro = "pagar" | "receber";
export type SituacaoDocumentoFinanceiro = "aberto" | "quitado" | "cancelado";

export type IntervaloParcelamento = "mensal" | "quinzenal" | "custom";

export type OpcoesParcelamento = {
  numeroParcelas: number;
  primeiraData: string;
  intervalo: IntervaloParcelamento;
  intervaloDiasCustom?: number;
};

export type ParcelaDocumento = {
  id: number;
  numero_parcela: number;
  total_parcelas: number;
  descricao: string;
  valor: string;
  valor_pago: string;
  saldo_restante: string;
  vencimento: string;
  situacao: SituacaoPagar | SituacaoReceber;
};

export type DocumentoFinanceiro = {
  id: number;
  tipo: TipoDocumentoFinanceiro;
  situacao: SituacaoDocumentoFinanceiro;
  fornecedor: number | null;
  nome_fornecedor: string | null;
  cliente: number | null;
  nome_cliente: string | null;
  descricao: string;
  valor_total: string;
  numero_parcelas: number;
  data_emissao: string;
  observacoes: string;
  parcelas: ParcelaDocumento[];
  criado_por: number | null;
  criado_em: string;
  atualizado_em: string;
};

export type CriarDocumentoFinanceiroPayload = {
  tipo: TipoDocumentoFinanceiro;
  fornecedor?: number | null;
  cliente?: number | null;
  descricao: string;
  valor_total: string;
  numero_parcelas: number;
  primeira_data: string;
  intervalo_dias: number;
  observacoes?: string;
};

export type LinhaContaReceber = {
  id?: number;
  produto: number | null;
  codigo_produto?: string | null;
  quantidade: string;
  unidade: ProductUnitCode;
  preco_unitario: string;
  desconto: string;
  total_linha: string;
};

export type LinhaContaPagar = {
  id: number;
  produto: number;
  codigo_produto: string;
  nome_produto: string;
  quantidade: string;
  unidade: ProductUnitCode;
  custo_unitario: string;
  total_linha: string;
};

export type ContaPagar = {
  id: number;
  documento: number | null;
  numero_parcela: number;
  total_parcelas: number;
  rotulo_parcela: string | null;
  fornecedor: number | null;
  nome_fornecedor: string | null;
  descricao: string;
  valor: string;
  valor_pago: string;
  saldo_restante: string;
  vencimento: string;
  situacao: SituacaoPagar;
  pago_em: string | null;
  observacoes: string;
  linhas?: LinhaContaPagar[];
  criado_por: number | null;
  criado_em: string;
  atualizado_em: string;
};

export type ContaReceber = {
  id: number;
  documento: number | null;
  numero_parcela: number;
  total_parcelas: number;
  rotulo_parcela: string | null;
  cliente: number | null;
  nome_cliente: string | null;
  descricao: string;
  data_emissao: string;
  valor: string;
  valor_pago: string;
  saldo_restante: string;
  vencimento: string;
  situacao: SituacaoReceber;
  recebido_em: string | null;
  observacoes: string;
  linhas?: LinhaContaReceber[];
  criado_por: number | null;
  criado_em: string;
  atualizado_em: string;
};

export type RespostaFluxoCaixa = {
  from: string;
  to: string;
  inflows: string;
  outflows: string;
  net: string;
};

export type AlertaContaPagar = {
  id: number;
  descricao: string;
  valor: string;
  vencimento: string;
  nome_fornecedor: string | null;
};

export type AlertaContaReceber = {
  id: number;
  descricao: string;
  valor: string;
  vencimento: string;
  nome_cliente: string | null;
};

export type RespostaAlertasFinanceiros = {
  today: string;
  days_ahead: number;
  until: string;
  overdue: {
    payables: AlertaContaPagar[];
    receivables: AlertaContaReceber[];
  };
  due_soon: {
    payables: AlertaContaPagar[];
    receivables: AlertaContaReceber[];
  };
};

export type HistoricoTituloParceiro = {
  id: number;
  descricao: string;
  data_emissao?: string;
  vencimento: string;
  valor: string;
  situacao: SituacaoPagar | SituacaoReceber;
  rotulo_parcela: string | null;
  recebido_em?: string | null;
  pago_em?: string | null;
};

export type ResumoHistoricoParceiro = Record<string, string>;

export type HistoricoParceiroResponse = {
  resumo: ResumoHistoricoParceiro;
  total: number;
  proximo: string | null;
  anterior: string | null;
  resultados: HistoricoTituloParceiro[];
};
