import type { PaginatedResponse } from "../types/catalog";
import type {
  ProductionRun,
  Recipe,
  StockAlertRow,
  StockBalanceRow,
  StockMovementRow,
} from "../types/stock";
import { apiDelete, apiGet, apiPatch, apiPost } from "./client";
import { toQuery } from "./catalog";

export async function listStockBalances(
  params: Record<string, string | number | boolean | undefined> = {},
): Promise<PaginatedResponse<StockBalanceRow>> {
  return apiGet<PaginatedResponse<StockBalanceRow>>(
    `/stock-balances/${toQuery(params)}`,
  );
}

export async function listStockMovements(
  params: Record<string, string | number | boolean | undefined> = {},
): Promise<PaginatedResponse<StockMovementRow>> {
  return apiGet<PaginatedResponse<StockMovementRow>>(
    `/stock-movements/${toQuery(params)}`,
  );
}

export type MovementCreatePayload = {
  movement_type: "purchase_in" | "adjustment";
  product: number;
  quantity: string;
  /** Unidade da quantidade (mesma categoria da unidade de cadastro do produto). Omitir = unidade base. */
  unit?: string;
  notes?: string;
};

export async function createStockMovement(
  body: MovementCreatePayload,
): Promise<StockMovementRow> {
  return apiPost<StockMovementRow>("/stock-movements/", body);
}

export async function listStockAlerts(
  params: Record<string, string | number | boolean | undefined> = {},
): Promise<PaginatedResponse<StockAlertRow>> {
  return apiGet<PaginatedResponse<StockAlertRow>>(
    `/stock-alerts/${toQuery(params)}`,
  );
}

export async function listRecipes(
  params: Record<string, string | number | boolean | undefined> = {},
): Promise<PaginatedResponse<Recipe>> {
  return apiGet<PaginatedResponse<Recipe>>(`/recipes/${toQuery(params)}`);
}

export async function getRecipe(id: number): Promise<Recipe> {
  return apiGet<Recipe>(`/recipes/${id}/`);
}

export async function createRecipe(body: {
  product: number;
  notes?: string;
  lines: Array<{
    component: number;
    quantity_per_unit: string;
    quantity_per_unit_unit?: string;
  }>;
}): Promise<Recipe> {
  return apiPost<Recipe>("/recipes/", body);
}

export async function updateRecipe(
  id: number,
  body: {
    product?: number;
    notes?: string;
    lines?: Array<{
      component: number;
      quantity_per_unit: string;
      quantity_per_unit_unit?: string;
    }>;
  },
): Promise<Recipe> {
  return apiPatch<Recipe>(`/recipes/${id}/`, body);
}

export async function deleteRecipe(id: number): Promise<void> {
  return apiDelete(`/recipes/${id}/`);
}

export async function listProductionRuns(
  params: Record<string, string | number | boolean | undefined> = {},
): Promise<PaginatedResponse<ProductionRun>> {
  return apiGet<PaginatedResponse<ProductionRun>>(
    `/production-runs/${toQuery(params)}`,
  );
}

export async function getProductionRun(id: number): Promise<ProductionRun> {
  return apiGet<ProductionRun>(`/production-runs/${id}/`);
}

export async function createProductionRun(body: {
  product: number;
  quantity_produced: string;
  quantity_produced_unit?: string;
  lines: Array<{
    component: number;
    quantity_consumed: string;
    quantity_consumed_unit?: string;
  }>;
  notes?: string;
}): Promise<ProductionRun> {
  return apiPost<ProductionRun>("/production-runs/", body);
}

/** Contagem rápida de alertas (uma página). */
export async function fetchStockAlertCount(): Promise<number> {
  const data = await apiGet<PaginatedResponse<StockAlertRow>>(
    "/stock-alerts/?page=1",
  );
  return data.count;
}
