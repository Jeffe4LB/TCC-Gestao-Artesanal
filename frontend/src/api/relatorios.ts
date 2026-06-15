import type {
  FormatoExportacao,
  RelatorioEnvelhecimentoFinanceiro,
  RelatorioEstoqueAbaixoMinimo,
  RelatorioEstoquePorCategoria,
  RelatorioFinanceiroEmAberto,
  RelatorioFluxoCaixa,
  RelatorioFluxoMensal,
  RelatorioMovimentacoesEstoque,
  RelatorioPosicaoEstoque,
  RelatorioReceitaPorProduto,
} from "../types/relatorios";
import { EXTENSAO_POR_FORMATO } from "../types/relatorios";
import { apiFetch, apiGet } from "./clienteHttp";
import { toQuery } from "./cadastro";

type ParametrosQuery = Record<string, string | number | boolean | undefined>;

/**
 * Baixa um relatório no formato indicado (csv | pdf | xlsx).
 *
 * - Faz `fetch` autenticado (JWT já é injetado por `apiFetch`).
 * - Converte a resposta em `Blob` e dispara o download no navegador.
 * - Respeita o nome de arquivo enviado pelo backend (`Content-Disposition`)
 *   quando presente; caso contrário, usa o `fallbackFilename`.
 */
async function baixarRelatorio(
  path: string,
  formato: FormatoExportacao,
  query: ParametrosQuery,
  fallbackFilename: string,
): Promise<void> {
  const q = { ...query, export: formato };
  const url = `${path}${toQuery(q)}`;
  const res = await apiFetch(url, { method: "GET" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    if (res.status === 401) throw new Error("Sessão expirada. Entre novamente.");
    const o = err as Record<string, unknown>;
    const detail = o.detail;
    const msg =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map(String).join(" ")
          : `Erro ao exportar relatório (${formato.toUpperCase()})`;
    throw new Error(msg);
  }
  const blob = await res.blob();
  const cd = res.headers.get("Content-Disposition");
  let nome = fallbackFilename;
  if (cd) {
    const m = /filename\*?=(?:UTF-8''|")?([^";]+)/i.exec(cd);
    if (m) nome = decodeURIComponent(m[1].replace(/"/g, "")).trim();
  }
  const extensao = `.${EXTENSAO_POR_FORMATO[formato]}`;
  if (!nome.toLowerCase().endsWith(extensao)) nome = `${nome}${extensao}`;
  const href = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = href;
  a.download = nome;
  a.click();
  URL.revokeObjectURL(href);
}

// ---------------------------------------------------------------------------
// Buscas (JSON)
// ---------------------------------------------------------------------------

export async function buscarRelatorioPosicaoEstoque(
  params: ParametrosQuery = {},
): Promise<RelatorioPosicaoEstoque> {
  return apiGet<RelatorioPosicaoEstoque>(
    `/relatorios/estoque/posicao/${toQuery(params)}`,
  );
}

export type ParametrosRelatorioMovimentacoes = {
  from: string;
  to: string;
  produto?: number;
  tipo_movimentacao?: string;
  limit?: number;
};

export async function buscarRelatorioMovimentacoesEstoque(
  params: ParametrosRelatorioMovimentacoes,
): Promise<RelatorioMovimentacoesEstoque> {
  return apiGet<RelatorioMovimentacoesEstoque>(
    `/relatorios/estoque/movimentacoes/${toQuery(params)}`,
  );
}

export async function buscarRelatorioEstoqueAbaixoMinimo(
  params: ParametrosQuery = {},
): Promise<RelatorioEstoqueAbaixoMinimo> {
  return apiGet<RelatorioEstoqueAbaixoMinimo>(
    `/relatorios/estoque/abaixo-minimo/${toQuery(params)}`,
  );
}

export async function buscarRelatorioFinanceiroEmAberto(): Promise<RelatorioFinanceiroEmAberto> {
  return apiGet<RelatorioFinanceiroEmAberto>("/relatorios/financeiro/em-aberto/");
}

export async function buscarRelatorioFluxoCaixa(
  de: string,
  ate: string,
): Promise<RelatorioFluxoCaixa> {
  return apiGet<RelatorioFluxoCaixa>(
    `/relatorios/financeiro/fluxo-caixa/${toQuery({ from: de, to: ate })}`,
  );
}

export async function buscarRelatorioEnvelhecimentoFinanceiro(): Promise<RelatorioEnvelhecimentoFinanceiro> {
  return apiGet<RelatorioEnvelhecimentoFinanceiro>("/relatorios/financeiro/envelhecimento/");
}

export type ParametrosReceitaPorProduto = {
  from: string;
  to: string;
  cliente?: number;
  categoria?: number;
};

export async function buscarRelatorioReceitaPorProduto(
  params: ParametrosReceitaPorProduto,
): Promise<RelatorioReceitaPorProduto> {
  return apiGet<RelatorioReceitaPorProduto>(
    `/relatorios/financeiro/receita-por-produto/${toQuery(params)}`,
  );
}

/**
 * Fluxo de caixa consolidado por mês (últimos N meses) para o gráfico de linha
 * do painel. `meses` é "clampado" para `[1, 60]` no backend.
 */
export async function buscarRelatorioFluxoMensal(
  meses = 12,
): Promise<RelatorioFluxoMensal> {
  return apiGet<RelatorioFluxoMensal>(
    `/relatorios/financeiro/fluxo-mensal/${toQuery({ meses })}`,
  );
}

/**
 * Estoque agregado por categoria — usado pelo gráfico de pizza do painel.
 */
export async function buscarRelatorioEstoquePorCategoria(): Promise<RelatorioEstoquePorCategoria> {
  return apiGet<RelatorioEstoquePorCategoria>("/relatorios/estoque/por-categoria/");
}

// ---------------------------------------------------------------------------
// Exportações genéricas (csv | pdf | xlsx)
// ---------------------------------------------------------------------------

export function exportarRelatorioPosicaoEstoque(
  formato: FormatoExportacao,
  params: ParametrosQuery = {},
): Promise<void> {
  return baixarRelatorio(
    "/relatorios/estoque/posicao/",
    formato,
    params,
    "relatorio-posicao-estoque",
  );
}

export function exportarRelatorioMovimentacoesEstoque(
  formato: FormatoExportacao,
  params: ParametrosRelatorioMovimentacoes,
): Promise<void> {
  return baixarRelatorio(
    "/relatorios/estoque/movimentacoes/",
    formato,
    params,
    "relatorio-movimentacoes-estoque",
  );
}

export function exportarRelatorioEstoqueAbaixoMinimo(
  formato: FormatoExportacao,
  params: ParametrosQuery = {},
): Promise<void> {
  return baixarRelatorio(
    "/relatorios/estoque/abaixo-minimo/",
    formato,
    params,
    "relatorio-estoque-abaixo-minimo",
  );
}

export function exportarRelatorioFinanceiroEmAberto(
  formato: FormatoExportacao,
): Promise<void> {
  return baixarRelatorio(
    "/relatorios/financeiro/em-aberto/",
    formato,
    {},
    "relatorio-financeiro-em-aberto",
  );
}

export function exportarRelatorioFluxoCaixa(
  formato: FormatoExportacao,
  de: string,
  ate: string,
): Promise<void> {
  return baixarRelatorio(
    "/relatorios/financeiro/fluxo-caixa/",
    formato,
    { from: de, to: ate },
    "relatorio-fluxo-caixa",
  );
}

export function exportarRelatorioEnvelhecimentoFinanceiro(
  formato: FormatoExportacao,
): Promise<void> {
  return baixarRelatorio(
    "/relatorios/financeiro/envelhecimento/",
    formato,
    {},
    "relatorio-envelhecimento",
  );
}

export function exportarRelatorioReceitaPorProduto(
  formato: FormatoExportacao,
  params: ParametrosReceitaPorProduto,
): Promise<void> {
  return baixarRelatorio(
    "/relatorios/financeiro/receita-por-produto/",
    formato,
    params,
    "relatorio-receita-por-produto",
  );
}

// ---------------------------------------------------------------------------
// Aliases legados (mantidos para compatibilidade com chamadas existentes)
// ---------------------------------------------------------------------------

export const baixarRelatorioPosicaoEstoqueCsv = (params: ParametrosQuery = {}) =>
  exportarRelatorioPosicaoEstoque("csv", params);

export const baixarRelatorioMovimentacoesEstoqueCsv = (
  params: ParametrosRelatorioMovimentacoes,
) => exportarRelatorioMovimentacoesEstoque("csv", params);

export const baixarRelatorioEstoqueAbaixoMinimoCsv = (params: ParametrosQuery = {}) =>
  exportarRelatorioEstoqueAbaixoMinimo("csv", params);

export const baixarRelatorioFinanceiroEmAbertoCsv = () =>
  exportarRelatorioFinanceiroEmAberto("csv");

export const baixarRelatorioFluxoCaixaCsv = (de: string, ate: string) =>
  exportarRelatorioFluxoCaixa("csv", de, ate);

export const baixarRelatorioEnvelhecimentoFinanceiroCsv = () =>
  exportarRelatorioEnvelhecimentoFinanceiro("csv");

export const baixarRelatorioReceitaPorProdutoCsv = (
  params: ParametrosReceitaPorProduto,
) => exportarRelatorioReceitaPorProduto("csv", params);
