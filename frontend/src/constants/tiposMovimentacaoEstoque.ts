/** Rótulos de `tipo_movimentacao` (valores da API em português). */
export const ROTULO_TIPO_MOVIMENTACAO: Record<string, string> = {
  entrada_compra: "Compra",
  ajuste: "Ajuste",
  consumo_producao: "Consumo (produção)",
  entrada_producao: "Entrada produto acabado",
  /** Legado — mesma movimentação que `entrada_producao`. */
  saida_producao: "Entrada produto acabado",
  venda_receber: "Venda (conta a receber)",
  estorno_venda_receber: "Estorno venda (conta a receber)",
  estorno_entrada_producao: "Estorno entrada (produção)",
  estorno_consumo_producao: "Estorno consumo (produção)",
};

export function rotuloTipoMovimentacao(codigo: string): string {
  return ROTULO_TIPO_MOVIMENTACAO[codigo] ?? codigo;
}

/** Opções para filtros de tipo de movimentação. */
export const OPCOES_FILTRO_TIPO_MOVIMENTACAO = [
  { value: "entrada_compra", label: ROTULO_TIPO_MOVIMENTACAO.entrada_compra },
  { value: "ajuste", label: ROTULO_TIPO_MOVIMENTACAO.ajuste },
  { value: "consumo_producao", label: ROTULO_TIPO_MOVIMENTACAO.consumo_producao },
  { value: "entrada_producao", label: ROTULO_TIPO_MOVIMENTACAO.entrada_producao },
  { value: "venda_receber", label: ROTULO_TIPO_MOVIMENTACAO.venda_receber },
  { value: "estorno_venda_receber", label: ROTULO_TIPO_MOVIMENTACAO.estorno_venda_receber },
  { value: "estorno_entrada_producao", label: ROTULO_TIPO_MOVIMENTACAO.estorno_entrada_producao },
  { value: "estorno_consumo_producao", label: ROTULO_TIPO_MOVIMENTACAO.estorno_consumo_producao },
] as const;
