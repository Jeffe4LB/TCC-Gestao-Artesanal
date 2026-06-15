/**
 * Utilitários comuns aos gráficos do painel:
 * - formatação de valores monetários em BRL;
 * - paleta de cores em harmonia com a UI Ant Design e com contraste suficiente
 *   para gráficos em modo claro.
 */

const formatadorBRL = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const formatadorCompactoBRL = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  notation: "compact",
  maximumFractionDigits: 1,
});

/** Converte string/número para Number, tolerante a vazio/NaN. */
export function paraNumero(v: string | number | null | undefined): number {
  if (v === null || v === undefined || v === "") return 0;
  const n = typeof v === "number" ? v : Number(v);
  return Number.isFinite(n) ? n : 0;
}

/** Formata valor monetário em pt-BR (ex.: `R$ 1.234,56`). */
export function formatarMoeda(v: string | number | null | undefined): string {
  return formatadorBRL.format(paraNumero(v));
}

/** Formata valor compacto (ex.: `R$ 1,2 mil`) — útil em eixos. */
export function formatarMoedaCompacta(v: string | number | null | undefined): string {
  return formatadorCompactoBRL.format(paraNumero(v));
}

export const CORES_GRAFICOS = {
  entradas: "#52c41a",
  saidas: "#ff4d4f",
  liquidoPositivo: "#1677ff",
  liquidoNeutro: "#8c8c8c",
  paletaPizza: [
    "#1677ff",
    "#52c41a",
    "#faad14",
    "#ff4d4f",
    "#722ed1",
    "#13c2c2",
    "#eb2f96",
    "#fa8c16",
    "#a0d911",
    "#2f54eb",
  ],
  aging: {
    vencidas: "#ff4d4f",
    vence_ate_7_dias: "#faad14",
    vence_8_a_30_dias: "#1677ff",
    vence_apos_30_dias: "#52c41a",
  },
} as const;

export const ROTULOS_FAIXA_AGING: Record<string, string> = {
  vencidas: "Vencidas",
  vence_ate_7_dias: "Vence em 7 dias",
  vence_8_a_30_dias: "Vence em 8–30 dias",
  vence_apos_30_dias: "Vence após 30 dias",
};
