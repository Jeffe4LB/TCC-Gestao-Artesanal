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
  unidade: string | null | undefined,
): string {
  if (qty == null || String(qty).trim() === "") return "—";
  const q = formatQuantityDisplay(qty);
  const u = (unidade ?? "").trim();
  return u ? `${q} ${u}` : q;
}

function parseQuantityNumber(value: string | number | null | undefined): number | null {
  if (value == null || value === "") return null;
  const s = String(value).trim().replace(",", ".");
  if (!s) return null;
  const n = Number(s);
  return Number.isFinite(n) ? n : null;
}

/**
 * Saldo na unidade base (KG, L, UN): valores com |q| &lt; 1 em peso/volume exibem em g ou ml.
 */
export function formatBalanceDisplay(
  qty: string | number | null | undefined,
  baseUnit: string | null | undefined,
): string {
  if (qty == null || String(qty).trim() === "") return "—";

  const n = parseQuantityNumber(qty);
  const u = (baseUnit ?? "").trim().toUpperCase();
  if (n === null || !u) return formatQuantityWithUnit(qty, baseUnit);

  const abs = Math.abs(n);
  if (u === "KG" && abs > 0 && abs < 1) {
    return `${formatQuantityDisplay(n * 1000)} g`;
  }
  if (u === "L" && abs > 0 && abs < 1) {
    return `${formatQuantityDisplay(n * 1000)} ml`;
  }
  return formatQuantityWithUnit(qty, baseUnit);
}
