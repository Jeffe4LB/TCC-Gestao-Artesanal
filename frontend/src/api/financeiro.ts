import type { PaginatedResponse } from "../types/cadastro";
import type {
  ContaPagar,
  ContaReceber,
  CriarDocumentoFinanceiroPayload,
  DocumentoFinanceiro,
  RespostaAlertasFinanceiros,
  RespostaFluxoCaixa,
} from "../types/financeiro";
import { apiDelete, apiGet, apiPatch, apiPost } from "./clienteHttp";
import { toQuery } from "./cadastro";

export async function listarContasPagar(
  params: Record<string, string | number | boolean | undefined> = {},
): Promise<PaginatedResponse<ContaPagar>> {
  return apiGet<PaginatedResponse<ContaPagar>>(`/contas-pagar/${toQuery(params)}`);
}

export async function criarContaPagar(body: Record<string, unknown>): Promise<ContaPagar> {
  return apiPost<ContaPagar>("/contas-pagar/", body);
}

export async function atualizarContaPagar(
  id: number,
  body: Record<string, unknown>,
): Promise<ContaPagar> {
  return apiPatch<ContaPagar>(`/contas-pagar/${id}/`, body);
}

export async function excluirContaPagar(id: number): Promise<void> {
  return apiDelete(`/contas-pagar/${id}/`);
}

export async function listarContasReceber(
  params: Record<string, string | number | boolean | undefined> = {},
): Promise<PaginatedResponse<ContaReceber>> {
  return apiGet<PaginatedResponse<ContaReceber>>(`/contas-receber/${toQuery(params)}`);
}

export async function criarContaReceber(body: Record<string, unknown>): Promise<ContaReceber> {
  return apiPost<ContaReceber>("/contas-receber/", body);
}

export async function atualizarContaReceber(
  id: number,
  body: Record<string, unknown>,
): Promise<ContaReceber> {
  return apiPatch<ContaReceber>(`/contas-receber/${id}/`, body);
}

export async function excluirContaReceber(id: number): Promise<void> {
  return apiDelete(`/contas-receber/${id}/`);
}

export async function obterFluxoCaixa(from: string, to: string): Promise<RespostaFluxoCaixa> {
  return apiGet<RespostaFluxoCaixa>(`/fluxo-caixa/${toQuery({ from, to })}`);
}

export async function obterAlertasFinanceiros(
  daysAhead = 7,
): Promise<RespostaAlertasFinanceiros> {
  return apiGet<RespostaAlertasFinanceiros>(
    `/alertas-financeiros/${toQuery({ days_ahead: daysAhead })}`,
  );
}

export async function contarVencidosFinanceiros(): Promise<number> {
  const data = await obterAlertasFinanceiros(7);
  return data.overdue.payables.length + data.overdue.receivables.length;
}

export async function listarDocumentosFinanceiros(
  params: Record<string, string | number | boolean | undefined> = {},
): Promise<PaginatedResponse<DocumentoFinanceiro>> {
  return apiGet<PaginatedResponse<DocumentoFinanceiro>>(
    `/documentos-financeiros/${toQuery(params)}`,
  );
}

export async function obterDocumentoFinanceiro(id: number): Promise<DocumentoFinanceiro> {
  return apiGet<DocumentoFinanceiro>(`/documentos-financeiros/${id}/`);
}

export async function criarDocumentoFinanceiro(
  body: CriarDocumentoFinanceiroPayload,
): Promise<DocumentoFinanceiro> {
  return apiPost<DocumentoFinanceiro>("/documentos-financeiros/", body);
}

export async function cancelarDocumentoFinanceiro(id: number): Promise<DocumentoFinanceiro> {
  return apiPost<DocumentoFinanceiro>(`/documentos-financeiros/${id}/cancelar/`, {});
}

export async function quitarParcelaDocumento(
  documentoId: number,
  body: { parcela_id: number; valor: string; data_pagamento: string },
): Promise<DocumentoFinanceiro> {
  return apiPost<DocumentoFinanceiro>(
    `/documentos-financeiros/${documentoId}/quitar-parcela/`,
    body,
  );
}
