import type { PaginatedResponse } from "../types/cadastro";
import type {
  AlertaEstoqueBaixo,
  LinhaEntradaCompraPayload,
  MovimentacaoEstoque,
  OrdemProducao,
  Receita,
  RespostaEntradaCompra,
  SaldoEstoque,
} from "../types/estoque";
import { apiDelete, apiGet, apiPatch, apiPost } from "./clienteHttp";
import { toQuery } from "./cadastro";

export async function listarSaldosEstoque(
  params: Record<string, string | number | boolean | undefined> = {},
): Promise<PaginatedResponse<SaldoEstoque>> {
  return apiGet<PaginatedResponse<SaldoEstoque>>(`/saldos-estoque/${toQuery(params)}`);
}

export async function listarMovimentacoesEstoque(
  params: Record<string, string | number | boolean | undefined> = {},
): Promise<PaginatedResponse<MovimentacaoEstoque>> {
  return apiGet<PaginatedResponse<MovimentacaoEstoque>>(
    `/movimentacoes-estoque/${toQuery(params)}`,
  );
}

export type PayloadCriarMovimentacao = {
  tipo_movimentacao: "ajuste";
  produto: number;
  quantidade: string;
  unidade?: string;
  observacoes?: string;
};

export async function criarEntradaCompra(body: {
  fornecedor?: number | null;
  descricao: string;
  vencimento: string;
  observacoes?: string;
  linhas: LinhaEntradaCompraPayload[];
}): Promise<RespostaEntradaCompra> {
  return apiPost<RespostaEntradaCompra>("/entradas-compra/", body);
}

export async function criarMovimentacaoEstoque(
  body: PayloadCriarMovimentacao,
): Promise<MovimentacaoEstoque> {
  return apiPost<MovimentacaoEstoque>("/movimentacoes-estoque/", body);
}

export async function listarAlertasEstoque(
  params: Record<string, string | number | boolean | undefined> = {},
): Promise<PaginatedResponse<AlertaEstoqueBaixo>> {
  return apiGet<PaginatedResponse<AlertaEstoqueBaixo>>(
    `/alertas-estoque/${toQuery(params)}`,
  );
}

export async function listarReceitas(
  params: Record<string, string | number | boolean | undefined> = {},
): Promise<PaginatedResponse<Receita>> {
  return apiGet<PaginatedResponse<Receita>>(`/receitas/${toQuery(params)}`);
}

export async function obterReceita(id: number): Promise<Receita> {
  return apiGet<Receita>(`/receitas/${id}/`);
}

export async function criarReceita(body: {
  produto: number;
  observacoes?: string;
  linhas: Array<{
    insumo: number;
    quantidade_por_unidade: string;
    quantidade_por_unidade_unidade?: string;
  }>;
}): Promise<Receita> {
  return apiPost<Receita>("/receitas/", body);
}

export async function atualizarReceita(
  id: number,
  body: {
    produto?: number;
    observacoes?: string;
    linhas?: Array<{
      insumo: number;
      quantidade_por_unidade: string;
      quantidade_por_unidade_unidade?: string;
    }>;
  },
): Promise<Receita> {
  return apiPatch<Receita>(`/receitas/${id}/`, body);
}

export async function excluirReceita(id: number): Promise<void> {
  return apiDelete(`/receitas/${id}/`);
}

export async function listarOrdensProducao(
  params: Record<string, string | number | boolean | undefined> = {},
): Promise<PaginatedResponse<OrdemProducao>> {
  return apiGet<PaginatedResponse<OrdemProducao>>(
    `/ordens-producao/${toQuery(params)}`,
  );
}

export async function obterOrdemProducao(id: number): Promise<OrdemProducao> {
  return apiGet<OrdemProducao>(`/ordens-producao/${id}/`);
}

export async function criarOrdemProducao(body: {
  produto: number;
  quantidade_produzida: string;
  quantidade_produzida_unidade?: string;
  linhas: Array<{
    insumo: number;
    quantidade_consumida: string;
    quantidade_consumida_unidade?: string;
  }>;
  observacoes?: string;
}): Promise<OrdemProducao> {
  return apiPost<OrdemProducao>("/ordens-producao/", body);
}

export async function cancelarOrdemProducao(id: number): Promise<OrdemProducao> {
  return apiPost<OrdemProducao>(`/ordens-producao/${id}/cancelar/`, {});
}

export async function contarAlertasEstoque(): Promise<number> {
  const data = await apiGet<PaginatedResponse<AlertaEstoqueBaixo>>(
    "/alertas-estoque/?page=1",
  );
  return data.total;
}

export type MovementCreatePayload = PayloadCriarMovimentacao;
