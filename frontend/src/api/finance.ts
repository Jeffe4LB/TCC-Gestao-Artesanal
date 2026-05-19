import type { PaginatedResponse } from "../types/catalog";
import type {
  AccountPayable,
  AccountReceivable,
  CashFlowResponse,
  FinanceAlertsResponse,
} from "../types/finance";
import { apiDelete, apiGet, apiPatch, apiPost } from "./client";
import { toQuery } from "./catalog";

export async function listAccountsPayable(
  params: Record<string, string | number | boolean | undefined> = {},
): Promise<PaginatedResponse<AccountPayable>> {
  return apiGet<PaginatedResponse<AccountPayable>>(
    `/accounts-payable/${toQuery(params)}`,
  );
}

export async function createAccountPayable(
  body: Record<string, unknown>,
): Promise<AccountPayable> {
  return apiPost<AccountPayable>("/accounts-payable/", body);
}

export async function updateAccountPayable(
  id: number,
  body: Record<string, unknown>,
): Promise<AccountPayable> {
  return apiPatch<AccountPayable>(`/accounts-payable/${id}/`, body);
}

export async function deleteAccountPayable(id: number): Promise<void> {
  return apiDelete(`/accounts-payable/${id}/`);
}

export async function listAccountsReceivable(
  params: Record<string, string | number | boolean | undefined> = {},
): Promise<PaginatedResponse<AccountReceivable>> {
  return apiGet<PaginatedResponse<AccountReceivable>>(
    `/accounts-receivable/${toQuery(params)}`,
  );
}

export async function createAccountReceivable(
  body: Record<string, unknown>,
): Promise<AccountReceivable> {
  return apiPost<AccountReceivable>("/accounts-receivable/", body);
}

export async function updateAccountReceivable(
  id: number,
  body: Record<string, unknown>,
): Promise<AccountReceivable> {
  return apiPatch<AccountReceivable>(`/accounts-receivable/${id}/`, body);
}

export async function deleteAccountReceivable(id: number): Promise<void> {
  return apiDelete(`/accounts-receivable/${id}/`);
}

export async function getCashFlow(
  from: string,
  to: string,
): Promise<CashFlowResponse> {
  return apiGet<CashFlowResponse>(
    `/cash-flow/${toQuery({ from, to })}`,
  );
}

export async function getFinanceAlerts(
  daysAhead = 7,
): Promise<FinanceAlertsResponse> {
  return apiGet<FinanceAlertsResponse>(
    `/finance-alerts/${toQuery({ days_ahead: daysAhead })}`,
  );
}

/** Soma de títulos vencidos (para badge no menu). */
export async function fetchFinanceOverdueCount(): Promise<number> {
  const data = await getFinanceAlerts(7);
  return (
    data.overdue.payables.length + data.overdue.receivables.length
  );
}
