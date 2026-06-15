/** Datas locais YYYY-MM-DD (sem deslocamento UTC). */

export function todayLocal(): string {
  const d = new Date();
  const y = d.getFullYear();
  const mo = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${mo}-${day}`;
}

export function firstDayOfMonthLocal(): string {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  return `${y}-${m}-01`;
}

export function formatarDataIso(d: Date): string {
  const y = d.getFullYear();
  const mo = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${mo}-${day}`;
}

export function intervaloUltimosDias(dias: number): { inicio: string; fim: string } {
  const fim = new Date();
  const inicio = new Date(fim);
  inicio.setDate(inicio.getDate() - dias);
  return { inicio: formatarDataIso(inicio), fim: formatarDataIso(fim) };
}
