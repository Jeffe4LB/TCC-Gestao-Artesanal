import { useMemo } from "react";
import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { LinhaEstoquePorCategoria } from "../../types/relatorios";
import { CORES_GRAFICOS, formatarMoeda, paraNumero } from "./utils";

type Props = {
  dados: LinhaEstoquePorCategoria[];
  altura?: number;
};

/**
 * Pizza com a distribuição de valor de estoque por categoria. As fatias usam
 * a paleta padrão do painel e o tooltip mostra valor + número de SKUs.
 */
export function GraficoEstoqueCategorias({ dados, altura = 300 }: Props) {
  const serie = useMemo(
    () =>
      dados.map((d, idx) => ({
        nome: d.categoria,
        valor: paraNumero(d.valor_estoque),
        skus: d.total_skus,
        cor: CORES_GRAFICOS.paletaPizza[idx % CORES_GRAFICOS.paletaPizza.length],
      })),
    [dados],
  );

  return (
    <ResponsiveContainer width="100%" height={altura}>
      <PieChart>
        <Pie
          data={serie}
          dataKey="valor"
          nameKey="nome"
          cx="50%"
          cy="50%"
          outerRadius="75%"
          innerRadius="40%"
          paddingAngle={2}
          label={({ percent }) =>
            percent && percent > 0.05 ? `${(percent * 100).toFixed(0)}%` : ""
          }
          labelLine={false}
        >
          {serie.map((entry) => (
            <Cell key={entry.nome} fill={entry.cor} />
          ))}
        </Pie>
        <Tooltip
          formatter={(value, _name, item) => {
            const payload = (item as { payload?: { nome?: string; skus?: number } } | undefined)
              ?.payload;
            return [
              `${formatarMoeda(value as number | string | null | undefined)} · ${
                payload?.skus ?? 0
              } SKU(s)`,
              payload?.nome ?? "",
            ];
          }}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
      </PieChart>
    </ResponsiveContainer>
  );
}
