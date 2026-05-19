import type {
  FinanceAgingReport,
  FinanceCashFlowReport,
  FinanceOpenReport,
  RevenueByProductReport,
  StockLowReport,
  StockMovementsReport,
  StockPositionReport,
} from "../types/reports";
import { apiFetch, apiGet } from "./client";
import { toQuery } from "./catalog";

async function downloadCsvAuthenticated(
  path: string,
  query: Record<string, string | number | boolean | undefined>,
  fallbackFilename: string,
): Promise<void> {
  const q = { ...query, export: "csv" };
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
          : "Erro ao baixar CSV";
    throw new Error(msg);
  }
  const blob = await res.blob();
  const cd = res.headers.get("Content-Disposition");
  let name = fallbackFilename;
  if (cd) {
    const m = /filename\*?=(?:UTF-8''|")?([^\";]+)/i.exec(cd);
    if (m) name = decodeURIComponent(m[1].replace(/"/g, "")).trim();
  }
  if (!name.toLowerCase().endsWith(".csv")) name = `${name}.csv`;
  const href = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = href;
  a.download = name;
  a.click();
  URL.revokeObjectURL(href);
}

export async function fetchStockPositionReport(
  params: Record<string, string | number | boolean | undefined> = {},
): Promise<StockPositionReport> {
  return apiGet<StockPositionReport>(
    `/reports/stock/position/${toQuery(params)}`,
  );
}

export type MovementReportParams = {
  from: string;
  to: string;
  product?: number;
  movement_type?: string;
  limit?: number;
};

export async function fetchStockMovementsReport(
  params: MovementReportParams,
): Promise<StockMovementsReport> {
  return apiGet<StockMovementsReport>(
    `/reports/stock/movements/${toQuery(params)}`,
  );
}

export async function fetchStockLowReport(
  params: Record<string, string | number | boolean | undefined> = {},
): Promise<StockLowReport> {
  return apiGet<StockLowReport>(`/reports/stock/low/${toQuery(params)}`);
}

export async function fetchFinanceOpenReport(): Promise<FinanceOpenReport> {
  return apiGet<FinanceOpenReport>("/reports/finance/open/");
}

export async function fetchFinanceCashFlowReport(
  from: string,
  to: string,
): Promise<FinanceCashFlowReport> {
  return apiGet<FinanceCashFlowReport>(
    `/reports/finance/cash-flow/${toQuery({ from, to })}`,
  );
}

export async function fetchFinanceAgingReport(): Promise<FinanceAgingReport> {
  return apiGet<FinanceAgingReport>("/reports/finance/aging/");
}

export type RevenueByProductParams = {
  from: string;
  to: string;
  customer?: number;
  category?: number;
};

export async function fetchRevenueByProductReport(
  params: RevenueByProductParams,
): Promise<RevenueByProductReport> {
  return apiGet<RevenueByProductReport>(
    `/reports/finance/revenue-by-product/${toQuery(params)}`,
  );
}

export function downloadStockPositionCsv(
  params: Record<string, string | number | boolean | undefined> = {},
): Promise<void> {
  return downloadCsvAuthenticated("/reports/stock/position/", params, "relatorio-posicao-estoque.csv");
}

export function downloadStockMovementsCsv(
  params: MovementReportParams,
): Promise<void> {
  return downloadCsvAuthenticated(
    "/reports/stock/movements/",
    params,
    "relatorio-movimentacoes-estoque.csv",
  );
}

export function downloadStockLowCsv(
  params: Record<string, string | number | boolean | undefined> = {},
): Promise<void> {
  return downloadCsvAuthenticated("/reports/stock/low/", params, "relatorio-estoque-abaixo-minimo.csv");
}

export function downloadFinanceOpenCsv(): Promise<void> {
  return downloadCsvAuthenticated("/reports/finance/open/", {}, "relatorio-financeiro-em-aberto.csv");
}

export function downloadFinanceCashFlowCsv(
  from: string,
  to: string,
): Promise<void> {
  return downloadCsvAuthenticated(
    "/reports/finance/cash-flow/",
    { from, to },
    "relatorio-fluxo-caixa.csv",
  );
}

export function downloadFinanceAgingCsv(): Promise<void> {
  return downloadCsvAuthenticated(
    "/reports/finance/aging/",
    {},
    "relatorio-envelhecimento.csv",
  );
}

export function downloadRevenueByProductCsv(
  params: RevenueByProductParams,
): Promise<void> {
  return downloadCsvAuthenticated(
    "/reports/finance/revenue-by-product/",
    params,
    "relatorio-receita-por-produto.csv",
  );
}
