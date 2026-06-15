import type { Produto } from "../types/cadastro";
import { coerceProductUnitCode, type ProductUnitCode } from "../constants/unidades";
import type { Receita } from "../types/estoque";
import { convertQuantitySameCategoria } from "./conversaoUnidade";
import { formatQuantityDisplay } from "./exibicaoQuantidade";

function parseQty(raw: string): number | null {
  const s = raw.trim().replace(",", ".");
  if (s === "") return null;
  const n = Number(s);
  return Number.isFinite(n) ? n : null;
}

/** Linhas do formulário de produção a partir da receita (totais da ordem). */
export function montarLinhasProducaoDaReceita(
  recipe: Receita,
  finished: Produto,
  productsById: Map<number, Produto>,
  qtyProducedStr: string,
  qtyProducedUnit: ProductUnitCode,
): Array<{ insumo: string; quantidade_consumida: string; quantidade_consumida_unidade: ProductUnitCode | "" }> {
  const cat = coerceProductUnitCode(finished.unidade);
  const qp = parseQty(qtyProducedStr);
  const nCat =
    qp != null && qp > 0 ? convertQuantitySameCategoria(qp, qtyProducedUnit, cat) : null;
  const factor = nCat != null && nCat > 0 ? nCat : 1;

  return recipe.linhas.map((l) => {
    const comp = productsById.get(l.insumo);
    const u: ProductUnitCode | "" = comp ? coerceProductUnitCode(comp.unidade) : "";
    const qtyPer = Number(String(l.quantidade_por_unidade).replace(",", "."));
    const total = (Number.isFinite(qtyPer) ? qtyPer : 0) * factor;
    return {
      insumo: String(l.insumo),
      quantidade_consumida: formatQuantityDisplay(String(total)),
      quantidade_consumida_unidade: u,
    };
  });
}

/** @deprecated Use `montarLinhasProducaoDaReceita`. */
export const buildProdutoionLinesFromReceita = montarLinhasProducaoDaReceita;
