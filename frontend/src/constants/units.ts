/**
 * Espelha backend `core.units` — unidades de medida (Fase 1).
 * Categorias: PESO (base KG), VOLUME (base L), UNIDADE (base UN).
 */

export type ProductUnitCode = "KG" | "G" | "L" | "ML" | "UN";

export type UnitCategoryCode = "PESO" | "VOLUME" | "UNIDADE";

export const UNIT_CATEGORY: Record<ProductUnitCode, UnitCategoryCode> = {
  KG: "PESO",
  G: "PESO",
  L: "VOLUME",
  ML: "VOLUME",
  UN: "UNIDADE",
};

export const PRODUCT_UNIT_OPTIONS: { value: ProductUnitCode; label: string }[] = [
  { value: "KG", label: "Quilo (KG)" },
  { value: "G", label: "Grama (G)" },
  { value: "L", label: "Litro (L)" },
  { value: "ML", label: "Mililitro (ML)" },
  { value: "UN", label: "Unidade (UN)" },
];

/** Unidade base da categoria (saldo de estoque — Fase 3). */
export function baseUnitForProductUnit(u: ProductUnitCode): ProductUnitCode {
  const c = UNIT_CATEGORY[u];
  if (c === "PESO") return "KG";
  if (c === "VOLUME") return "L";
  return "UN";
}

export function compatibleUnitsForProduct(u: ProductUnitCode): ProductUnitCode[] {
  const cat = UNIT_CATEGORY[u];
  return PRODUCT_UNIT_OPTIONS.filter((o) => UNIT_CATEGORY[o.value] === cat).map((o) => o.value);
}

export const DEFAULT_PRODUCT_UNIT: ProductUnitCode = "UN";

const CODES = new Set<string>(PRODUCT_UNIT_OPTIONS.map((o) => o.value));

/** Normaliza resposta da API (ex.: legado `un`) para código canônico. */
export function coerceProductUnitCode(raw: string | undefined | null): ProductUnitCode {
  const s = (raw ?? "").trim();
  if (!s) return DEFAULT_PRODUCT_UNIT;
  const upper = s.toUpperCase();
  if (CODES.has(upper)) return upper as ProductUnitCode;
  if (s.toLowerCase() === "un") return "UN";
  return DEFAULT_PRODUCT_UNIT;
}
