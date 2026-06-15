const FORMATADOR_BRL = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
});

export function formatarBRL(valor: number | string): string {
  const num = typeof valor === "string" ? Number(String(valor).replace(",", ".")) : valor;
  return FORMATADOR_BRL.format(Number.isFinite(num) ? num : 0);
}

export function paraDecimalSeguro(raw: string | undefined): number {
  const n = Number(String(raw ?? "").trim().replace(",", "."));
  return Number.isFinite(n) ? n : 0;
}
