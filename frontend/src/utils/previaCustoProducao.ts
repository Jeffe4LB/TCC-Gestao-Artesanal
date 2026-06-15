import type { Produto } from "../types/cadastro";
import { coerceProductUnitCode, PRODUCT_UNIT_OPTIONS, type ProductUnitCode } from "../constants/unidades";
import { convertQuantitySameCategoria } from "./conversaoUnidade";
import { formatarBRL as formatarBRLMoeda } from "./moeda";

export { formatarBRL } from "./moeda";

export type LinhaFormularioProducao = {
  insumo: string;
  quantidade_consumida: string;
  quantidade_consumida_unidade: ProductUnitCode | "";
};

/** @deprecated Use `LinhaFormularioProducao`. */
export type ProdutoionFormLine = LinhaFormularioProducao;

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
 * Estima custo dos insumos desta ordem (Σ qtd na unidade de cadastro do insumo × custo_unitario)
 * e custo unitário implícito do lote: **total ÷ quantidade produzida na unidade selecionada** no formulário.
 *
 * Insumos: `custo_unitario` na API é por 1 unidade de **cadastro** do insumo; a qtd informada (na unidade do menu)
 * é convertida para cadastro antes de multiplicar.
 */
export function estimarPreviaCustoProducao(input: {
  producedProduto: Produto | undefined;
  qtyProducedStr: string;
  qtyProducedUnit: ProductUnitCode;
  linhas: LinhaFormularioProducao[];
  componentsCatalog: Produto[];
}): {
  materialsTotal: number;
  impliedUnitCost: number | null;
  /** Unidade do menu usada no rótulo do custo implícito (= quantidade produzida). */
  impliedOutputUnit: ProductUnitCode | null;
  hasValidLines: boolean;
} {
  const { producedProduto, qtyProducedStr, qtyProducedUnit, linhas, componentsCatalog } = input;
  const byId = new Map(componentsCatalog.map((p) => [String(p.id), p]));

  let materialsTotal = 0;
  let hasValidLines = false;

  for (const row of linhas) {
    const id = row.insumo.trim();
    if (!id) continue;
    const comp = byId.get(id);
    if (!comp) continue;
    const q = parseQty(row.quantidade_consumida);
    if (q == null || q <= 0) continue;

    const catalogUnit = coerceProductUnitCode(comp.unidade);
    const fromUnit = row.quantidade_consumida_unidade || catalogUnit;
    const qtyCat = convertQuantitySameCategoria(q, fromUnit, catalogUnit);
    if (qtyCat == null || !Number.isFinite(qtyCat) || qtyCat < 0) continue;

    hasValidLines = true;
    materialsTotal += qtyCat * parseMoney(comp.custo_unitario);
  }

  materialsTotal = roundMoney2(materialsTotal);

  let impliedUnitCost: number | null = null;
  let impliedOutputUnit: ProductUnitCode | null = null;

  if (producedProduto) {
    const qp = parseQty(qtyProducedStr);
    if (qp != null && qp > 0) {
      impliedUnitCost = roundMoney2(materialsTotal / qp);
      impliedOutputUnit = qtyProducedUnit;
    }
  }

  return { materialsTotal, impliedUnitCost, impliedOutputUnit, hasValidLines };
}

/** @deprecated Use `estimarPreviaCustoProducao`. */
export const estimateProdutoionCostPreview = estimarPreviaCustoProducao;

/** @deprecated Use `formatarBRL` de `utils/moeda`. */
export const formatBRL = formatarBRLMoeda;
