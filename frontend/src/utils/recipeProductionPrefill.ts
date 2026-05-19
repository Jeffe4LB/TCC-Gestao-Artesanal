import type { Product } from "../types/catalog";
import { coerceProductUnitCode, type ProductUnitCode } from "../constants/units";
import type { Recipe } from "../types/stock";
import { convertQuantitySameCategory } from "./unitConversion";
import { formatQuantityDisplay } from "./quantityDisplay";

function parseQty(raw: string): number | null {
  const s = raw.trim().replace(",", ".");
  if (s === "") return null;
  const n = Number(s);
  return Number.isFinite(n) ? n : null;
}

/** Linhas do formulário de produção a partir da receita (totais da ordem). */
export function buildProductionLinesFromRecipe(
  recipe: Recipe,
  finished: Product,
  productsById: Map<number, Product>,
  qtyProducedStr: string,
  qtyProducedUnit: ProductUnitCode,
): Array<{ component: string; quantity_consumed: string; quantity_consumed_unit: ProductUnitCode | "" }> {
  const cat = coerceProductUnitCode(finished.unit);
  const qp = parseQty(qtyProducedStr);
  const nCat =
    qp != null && qp > 0 ? convertQuantitySameCategory(qp, qtyProducedUnit, cat) : null;
  const factor = nCat != null && nCat > 0 ? nCat : 1;

  return recipe.lines.map((l) => {
    const comp = productsById.get(l.component);
    const u: ProductUnitCode | "" = comp ? coerceProductUnitCode(comp.unit) : "";
    const qtyPer = Number(String(l.quantity_per_unit).replace(",", "."));
    const total = (Number.isFinite(qtyPer) ? qtyPer : 0) * factor;
    return {
      component: String(l.component),
      quantity_consumed: formatQuantityDisplay(String(total)),
      quantity_consumed_unit: u,
    };
  });
}
