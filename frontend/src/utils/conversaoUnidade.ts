/**
 * Conversão na mesma categoria (espelha backend `core.units.FACTOR_TO_BASE`).
 */
import { UNIT_CATEGORY, type ProductUnitCode } from "../constants/unidades";

const FACTOR_TO_BASE: Record<ProductUnitCode, number> = {
  KG: 1,
  G: 0.001,
  L: 1,
  ML: 0.001,
  UN: 1,
};

export function convertQuantitySameCategoria(
  qty: number,
  fromUnit: ProductUnitCode,
  toUnit: ProductUnitCode,
): number | null {
  if (UNIT_CATEGORY[fromUnit] !== UNIT_CATEGORY[toUnit]) return null;
  const base = qty * FACTOR_TO_BASE[fromUnit];
  return base / FACTOR_TO_BASE[toUnit];
}
