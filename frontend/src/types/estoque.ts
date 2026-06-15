export type SaldoEstoque = {
  id: number;
  produto: number;
  codigo_produto: string;
  nome_produto: string;
  quantidade: string;
  unidade_base?: string;
};

import type { ContaPagar, LinhaContaPagar } from "./financeiro";

export type MovimentacaoEstoque = {
  id: number;
  produto: number;
  codigo_produto: string;
  delta_quantidade: string;
  quantidade_informada?: string | null;
  unidade_informada?: string | null;
  unidade_base?: string;
  tipo_movimentacao: string;
  ordem_producao: number | null;
  conta_pagar?: number | null;
  observacoes: string;
  criado_por: number | null;
  criado_por_nome?: string | null;
  criado_em: string;
};

export type LinhaEntradaCompraPayload = {
  produto: number;
  quantidade: string;
  unidade?: string;
  custo_unitario?: string;
};

export type RespostaEntradaCompra = {
  conta_pagar: ContaPagar;
  linhas: LinhaContaPagar[];
  movimentacoes: MovimentacaoEstoque[];
};

export type AlertaEstoqueBaixo = {
  id_produto: number;
  codigo: string;
  nome: string;
  estoque_minimo: string;
  quantidade_atual: string;
  deficit: string;
  unidade_base?: string;
};

export type LinhaReceita = {
  id?: number;
  insumo: number;
  codigo_insumo?: string;
  quantidade_por_unidade: string;
};

export type Receita = {
  id: number;
  produto: number;
  observacoes: string;
  linhas: LinhaReceita[];
  criado_em: string;
  atualizado_em: string;
};

export type LinhaOrdemProducao = {
  id: number;
  insumo: number;
  codigo_insumo: string;
  nome_insumo: string;
  quantidade_consumida: string;
};

export type OrdemProducao = {
  id: number;
  produto: number;
  codigo_produto: string;
  nome_produto: string;
  quantidade_produzida: string;
  observacoes: string;
  linhas: LinhaOrdemProducao[];
  criado_por: number | null;
  criado_em: string;
  cancelada_em: string | null;
  cancelada_por: number | null;
  ativa?: boolean;
};

export function ordemProducaoAtiva(run: OrdemProducao): boolean {
  return run.ativa ?? !run.cancelada_em;
}
