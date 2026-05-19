/**
 * Formata quantidades vindas da API (Decimal com até 3 casas, separador `.`).
 * Remove zeros à direita para não parecer "dez mil" em pt-BR (ex.: `10.000` → `10`).
 */
export function formatQuantityDisplay(
  value: string | number | null | undefined,
  options?: { emptyAs?: string },
): string {
  const empty = options?.emptyAs ?? "—";
  if (value == null || value === "") return empty;

  let s = String(value).trim().replace(",", ".");
  if (!s) return empty;

  const neg = s.startsWith("-");
  if (neg) s = s.slice(1);

  const dotIdx = s.indexOf(".");
  if (dotIdx === -1) {
    if (!/^\d+$/.test(s)) return (neg ? "-" : "") + s;
    const intOnly = String(parseInt(s, 10));
    return (neg ? "-" : "") + (Number.isNaN(Number(intOnly)) ? s : intOnly);
  }

  let intPart = s.slice(0, dotIdx);
  if (intPart === "" || !/^\d+$/.test(intPart)) return (neg ? "-" : "") + s;
  intPart = String(parseInt(intPart, 10));
  if (Number.isNaN(Number(intPart))) intPart = "0";

  const fracRaw = s.slice(dotIdx + 1).replace(/[^0-9]/g, "");
  const fracTrimmed = fracRaw.replace(/0+$/, "");
  if (!fracTrimmed) return (neg ? "-" : "") + intPart;
  return (neg ? "-" : "") + `${intPart}.${fracTrimmed}`;
}

/** Quantidade + unidade (ex.: `10 KG`). */
export function formatQuantityWithUnit(
  qty: string | number | null | undefined,
  unit: string | null | undefined,
): string {
  if (qty == null || String(qty).trim() === "") return "—";
  const q = formatQuantityDisplay(qty);
  const u = (unit ?? "").trim();
  return u ? `${q} ${u}` : q;
}
