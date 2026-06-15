import { useMemo } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { PontoFluxoMensal } from "../../types/relatorios";
import { CORES_GRAFICOS, formatarMoeda, formatarMoedaCompacta, paraNumero } from "./utils";

type Props = {
  dados: PontoFluxoMensal[];
  altura?: number;
};

type LinhaGrafico = {
  mes: string;
  entradas: number;
  saidas: number;
  liquido: number;
};

/**
 * Gráfico de linha com 3 séries: entradas (verde), saídas (vermelho) e
 * líquido (azul). Eixo X usa o rótulo curto (`jun/2026`), tooltip usa BRL.
 */
export function GraficoFluxoMensal({ dados, altura = 300 }: Props) {
  const serie = useMemo<LinhaGrafico[]>(
    () =>
      dados.map((d) => ({
        mes: d.mes_rotulo,
        entradas: paraNumero(d.entradas),
        saidas: paraNumero(d.saidas),
        liquido: paraNumero(d.liquido),
      })),
    [dados],
  );

  return (
    <ResponsiveContainer width="100%" height={altura}>
      <LineChart data={serie} margin={{ top: 8, right: 16, left: 8, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="mes" tick={{ fontSize: 12 }} />
        <YAxis
          tick={{ fontSize: 12 }}
          tickFormatter={(v) => formatarMoedaCompacta(v as number)}
        />
        <Tooltip
          formatter={(value) => formatarMoeda(value as number | string | null | undefined)}
          labelFormatter={(label) => `Mês: ${String(label)}`}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Line
          type="monotone"
          name="Entradas"
          dataKey="entradas"
          stroke={CORES_GRAFICOS.entradas}
          strokeWidth={2}
          dot={{ r: 3 }}
          activeDot={{ r: 5 }}
        />
        <Line
          type="monotone"
          name="Saídas"
          dataKey="saidas"
          stroke={CORES_GRAFICOS.saidas}
          strokeWidth={2}
          dot={{ r: 3 }}
          activeDot={{ r: 5 }}
        />
        <Line
          type="monotone"
          name="Líquido"
          dataKey="liquido"
          stroke={CORES_GRAFICOS.liquidoPositivo}
          strokeWidth={2}
          strokeDasharray="4 2"
          dot={{ r: 3 }}
          activeDot={{ r: 5 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
