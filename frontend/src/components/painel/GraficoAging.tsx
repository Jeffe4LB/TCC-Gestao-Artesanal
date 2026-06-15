import { useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { RelatorioEnvelhecimentoFinanceiro } from "../../types/relatorios";
import {
  CORES_GRAFICOS,
  ROTULOS_FAIXA_AGING,
  formatarMoeda,
  formatarMoedaCompacta,
  paraNumero,
} from "./utils";

type Props = {
  dados: RelatorioEnvelhecimentoFinanceiro;
  altura?: number;
};

const FAIXAS = [
  "vencidas",
  "vence_ate_7_dias",
  "vence_8_a_30_dias",
  "vence_apos_30_dias",
] as const;

/**
 * Barra empilhada (1 barra para "Pagar" e 1 para "Receber") mostrando o valor
 * total em cada faixa de envelhecimento. Cores: vencidas em vermelho, próximas
 * em laranja, médio prazo em azul e longo prazo em verde.
 */
export function GraficoAging({ dados, altura = 300 }: Props) {
  const serie = useMemo(() => {
    const total = (origem: Record<string, { total: string }>) =>
      FAIXAS.reduce((acc, f) => {
        acc[f] = paraNumero(origem?.[f]?.total ?? "0");
        return acc;
      }, {} as Record<string, number>);

    return [
      { categoria: "A pagar", ...total(dados.pagar) },
      { categoria: "A receber", ...total(dados.receber) },
    ];
  }, [dados]);

  return (
    <ResponsiveContainer width="100%" height={altura}>
      <BarChart data={serie} margin={{ top: 8, right: 16, left: 8, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="categoria" tick={{ fontSize: 12 }} />
        <YAxis
          tick={{ fontSize: 12 }}
          tickFormatter={(v) => formatarMoedaCompacta(v as number)}
        />
        <Tooltip
          formatter={(value) => formatarMoeda(value as number | string | null | undefined)}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        {FAIXAS.map((faixa) => (
          <Bar
            key={faixa}
            dataKey={faixa}
            stackId="aging"
            name={ROTULOS_FAIXA_AGING[faixa]}
            fill={CORES_GRAFICOS.aging[faixa]}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
