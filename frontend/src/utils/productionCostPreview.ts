import type { Product } from "../types/catalog";
import { coerceProductUnitCode, PRODUCT_UNIT_OPTIONS, type ProductUnitCode } from "../constants/units";
import { convertQuantitySameCategory } from "./unitConversion";

export type ProductionFormLine = {
  component: string;
  quantity_consumed: string;
  quantity_consumed_unit: ProductUnitCode | "";
};

function parseQty(raw: string): number | null {
  const s = raw.trim().replace(",", ".");
  if (s === "") return null;
  const n = Number(s);
  return Number.isFinite(n) ? n : null;
}

function parseMoney(raw: string): number {
  const n = Number(String(raw).trim().replace(",", "."));
  return Number.isFinite(n) ? n : 0;
}

function roundMoney2(n: number): number {
  return Math.round(n * 100 + 1e-9) / 100;
}

export function unitLabel(code: ProductUnitCode): string {
  return PRODUCT_UNIT_OPTIONS.find((o) => o.value === code)?.label ?? code;
}

/**
 * Estima custo dos insumos desta ordem (Σ qtd na unidade de cadastro do insumo × unit_cost)
 * e custo unitário implícito do lote: **total ÷ quantidade produzida na unidade selecionada** no formulário.
 *
 * Insumos: `unit_cost` na API é por 1 unidade de **cadastro** do insumo; a qtd informada (na unidade do menu)
 * é convertida para cadastro antes de multiplicar.
 */
export function estimateProductionCostPreview(input: {
  producedProduct: Product | undefined;
  qtyProducedStr: string;
  qtyProducedUnit: ProductUnitCode;
  lines: ProductionFormLine[];
  componentsCatalog: Product[];
}): {
  materialsTotal: number;
  impliedUnitCost: number | null;
  /** Unidade do menu usada no rótulo do custo implícito (= quantidade produzida). */
  impliedOutputUnit: ProductUnitCode | null;
  hasValidLines: boolean;
} {
  const { producedProduct, qtyProducedStr, qtyProducedUnit, lines, componentsCatalog } = input;
  const byId = new Map(componentsCatalog.map((p) => [String(p.id), p]));

  let materialsTotal = 0;
  let hasValidLines = false;

  for (const row of lines) {
    const id = row.component.trim();
    if (!id) continue;
    const comp = byId.get(id);
    if (!comp) continue;
    const q = parseQty(row.quantity_consumed);
    if (q == null || q <= 0) continue;

    const catalogUnit = coerceProductUnitCode(comp.unit);
    const fromUnit = row.quantity_consumed_unit || catalogUnit;
    const qtyCat = convertQuantitySameCategory(q, fromUnit, catalogUnit);
    if (qtyCat == null || !Number.isFinite(qtyCat) || qtyCat < 0) continue;

    hasValidLines = true;
    materialsTotal += qtyCat * parseMoney(comp.unit_cost);
  }

  materialsTotal = roundMoney2(materialsTotal);

  let impliedUnitCost: number | null = null;
  let impliedOutputUnit: ProductUnitCode | null = null;

  if (producedProduct) {
    const qp = parseQty(qtyProducedStr);
    if (qp != null && qp > 0) {
      impliedUnitCost = roundMoney2(materialsTotal / qp);
      impliedOutputUnit = qtyProducedUnit;
    }
  }

  return { materialsTotal, impliedUnitCost, impliedOutputUnit, hasValidLines };
}

export function formatBRL(value: number): string {
  return value.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}
