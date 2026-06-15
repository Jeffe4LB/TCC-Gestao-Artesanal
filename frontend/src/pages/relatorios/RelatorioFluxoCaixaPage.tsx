import { useCallback, useEffect, useState } from "react";
import { DatePicker, Space, Spin } from "antd";
import dayjs from "dayjs";
import {
  buscarRelatorioFluxoCaixa,
  exportarRelatorioFluxoCaixa,
} from "../../api/relatorios";
import { LayoutRelatorio } from "../../components/relatorios/LayoutRelatorio";
import { ResumoRelatorio } from "../../components/relatorios/ResumoRelatorio";
import type { FormatoExportacao, RelatorioFluxoCaixa } from "../../types/relatorios";
import { firstDayOfMonthLocal, todayLocal } from "./intervaloDatas";

export function RelatorioFluxoCaixaPage() {
  const [from, setFrom] = useState(firstDayOfMonthLocal);
  const [to, setTo] = useState(todayLocal);
  const [data, setData] = useState<RelatorioFluxoCaixa | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const res = await buscarRelatorioFluxoCaixa(from, to);
      setData(res);
    } catch (e) {
      setData(null);
      setErr(e instanceof Error ? e.message : "Erro ao gerar");
    } finally {
      setLoading(false);
    }
  }, [from, to]);

  useEffect(() => {
    void load();
  }, [load]);

  const exportar = async (formato: FormatoExportacao) => {
    setExporting(true);
    setErr(null);
    try {
      await exportarRelatorioFluxoCaixa(formato, from, to);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao exportar");
    } finally {
      setExporting(false);
    }
  };

  return (
    <LayoutRelatorio
      titulo="Fluxo de caixa"
      descricao="Mesma regra do módulo financeiro: entradas e saídas pela data efetiva (recebido/pago)."
      periodo={data ? `${data.de} a ${data.ate}` : undefined}
      filtros={
        <Space wrap>
          <DatePicker
            format="YYYY-MM-DD"
            value={dayjs(from)}
            onChange={(_, s) => setFrom(typeof s === "string" && s ? s : firstDayOfMonthLocal())}
          />
          <DatePicker
            format="YYYY-MM-DD"
            value={dayjs(to)}
            onChange={(_, s) => setTo(typeof s === "string" && s ? s : todayLocal())}
          />
        </Space>
      }
      onAtualizar={() => void load()}
      onExportarFormato={exportar}
      loadingAtualizar={loading}
      loadingExportar={exporting}
      textoAtualizar="Atualizar prévia"
      erro={err}
    >
      <Spin spinning={loading && !data}>
        {data ? (
          <ResumoRelatorio
            itens={[
              { key: "ent", titulo: "Entradas", valor: data.entradas, prefixo: "R$ " },
              { key: "sai", titulo: "Saídas", valor: data.saidas, prefixo: "R$ " },
              { key: "liq", titulo: "Líquido", valor: data.liquido, prefixo: "R$ " },
            ]}
          />
        ) : null}
      </Spin>
    </LayoutRelatorio>
  );
}
