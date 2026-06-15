import type { IntervaloParcelamento } from "../../types/financeiro";

export type LinhaPreviewParcela = {
  numero: number;
  valor: string;
  vencimento: string;
};

export function intervaloParaDias(
  intervalo: IntervaloParcelamento,
  customDias?: number,
): number {
  if (intervalo === "quinzenal") return 15;
  if (intervalo === "custom") return Math.max(0, customDias ?? 30);
  return 30;
}

/** Replica a regra do backend: divide o total e ajusta a última parcela. */
export function gerarPreviewParcelas(
  valorTotal: number,
  numeroParcelas: number,
  primeiraData: string,
  intervaloDias: number,
): LinhaPreviewParcela[] {
  if (!primeiraData || numeroParcelas < 1 || valorTotal <= 0) return [];

  const valorParcela = Math.round((valorTotal / numeroParcelas) * 100) / 100;
  const linhas: LinhaPreviewParcela[] = [];
  let soma = 0;
  const base = new Date(`${primeiraData}T12:00:00`);

  for (let i = 0; i < numeroParcelas; i++) {
    const venc = new Date(base);
    venc.setDate(venc.getDate() + intervaloDias * i);
    const y = venc.getFullYear();
    const m = String(venc.getMonth() + 1).padStart(2, "0");
    const d = String(venc.getDate()).padStart(2, "0");
    let valor: number;
    if (i < numeroParcelas - 1) {
      valor = valorParcela;
      soma += valor;
    } else {
      valor = Math.round((valorTotal - soma) * 100) / 100;
    }
    linhas.push({
      numero: i + 1,
      valor: valor.toFixed(2),
      vencimento: `${y}-${m}-${d}`,
    });
  }
  return linhas;
}
