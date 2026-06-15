import { useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { CORES_GRAFICOS, formatarMoeda, formatarMoedaCompacta, paraNumero } from "./utils";

export type LinhaTopProduto = {
  sku: string;
  nome: string;
  faturamento_total: string;
  lucro: string;
  margem_percentual: string;
};

type Props = {
  dados: LinhaTopProduto[];
  /** Mostra `top` primeiras barras (após ordenar por lucro desc). */
  top?: number;
  altura?: number;
};

/**
 * Barra horizontal com os N produtos mais lucrativos. A barra mostra o lucro
 * (positivo em verde, negativo em vermelho) e o tooltip detalha faturamento e
 * margem.
 */
export function GraficoTopProdutos({ dados, top = 5, altura = 300 }: Props) {
  const serie = useMemo(() => {
    return [...dados]
      .map((d) => ({
        rotulo: `${d.sku} — ${d.nome.length > 22 ? d.nome.slice(0, 22) + "…" : d.nome}`,
        sku: d.sku,
        nome: d.nome,
        lucro: paraNumero(d.lucro),
        faturamento: paraNumero(d.faturamento_total),
        margem: paraNumero(d.margem_percentual),
      }))
      .sort((a, b) => b.lucro - a.lucro)
      .slice(0, top);
  }, [dados, top]);

  return (
    <ResponsiveContainer width="100%" height={altura}>
      <BarChart
        data={serie}
        layout="vertical"
        margin={{ top: 8, right: 16, left: 8, bottom: 0 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis
          type="number"
          tick={{ fontSize: 12 }}
          tickFormatter={(v) => formatarMoedaCompacta(v as number)}
        />
        <YAxis
          type="category"
          dataKey="rotulo"
          tick={{ fontSize: 12 }}
          width={180}
        />
        <Tooltip
          formatter={(value, name, item) => {
            if (name === "Lucro") {
              return [formatarMoeda(value as number | string | null | undefined), name];
            }
            const payload = (item as
              | { payload?: { faturamento?: number; margem?: number } }
              | undefined)?.payload;
            return [
              `${formatarMoeda(payload?.faturamento ?? 0)} · margem ${payload?.margem ?? 0}%`,
              "Detalhes",
            ];
          }}
        />
        <Bar dataKey="lucro" name="Lucro" radius={[0, 4, 4, 0]}>
          {serie.map((entry) => (
            <Cell
              key={entry.sku}
              fill={entry.lucro >= 0 ? CORES_GRAFICOS.entradas : CORES_GRAFICOS.saidas}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
