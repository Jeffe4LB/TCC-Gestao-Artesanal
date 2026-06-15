import type { Produto } from "../../../types/cadastro";
import type { LinhaContaReceber } from "../../../types/financeiro";
import { coerceProductUnitCode } from "../../../constants/unidades";
import type { LinhaFormContaReceber } from "./types";

export const COLUNA_DATA_ISO = {
  width: 120,
  className: "celula-data-iso",
  onCell: () => ({ className: "celula-data-iso" }),
  onHeaderCell: () => ({ className: "celula-data-iso" }),
} as const;

export const FORM_ITEM_DATA = { minWidth: 140, marginBottom: 0 } as const;

const moneyStr = (v: string | undefined) => (v == null || v === "" ? "0" : v);

export function parseDecimal(raw: string | undefined): number | null {
  const t = (raw ?? "").trim().replace(",", ".");
  if (t === "") return null;
  const n = Number(t);
  if (!Number.isFinite(n)) return null;
  return n;
}

export function totalLinha(q: string, price: string, disc: string): number {
  const a = Number(q) || 0;
  const b = Number(price) || 0;
  const d = Number(disc) || 0;
  return Math.round((a * b - d) * 100) / 100;
}

export function isPrecoUnitarioVazio(preco: string): boolean {
  const n = parseDecimal(preco);
  return preco.trim() === "" || n === null || n <= 0;
}

export function precoCatalogoParaLinha(produto: Produto): string | null {
  const n = parseDecimal(produto.preco_venda);
  if (n === null || n <= 0) return null;
  return moneyStr(produto.preco_venda);
}

export function mapApiLineToForm(l: LinhaContaReceber): LinhaFormContaReceber {
  const u = coerceProductUnitCode(l.unidade);
  return {
    produto: l.produto != null ? String(l.produto) : "",
    quantidade: String(l.quantidade),
    unidade: u,
    preco_unitario: l.preco_unitario,
    desconto: l.desconto ?? "0",
  };
}
