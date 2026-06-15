import { useCallback, useEffect, useMemo, useState } from "react";
import { Spin, Table, Typography } from "antd";
import {
  buscarRelatorioEnvelhecimentoFinanceiro,
  exportarRelatorioEnvelhecimentoFinanceiro,
} from "../../api/relatorios";
import { LayoutRelatorio } from "../../components/relatorios/LayoutRelatorio";
import { ResumoRelatorio } from "../../components/relatorios/ResumoRelatorio";
import type {
  FormatoExportacao,
  RelatorioEnvelhecimentoFinanceiro,
} from "../../types/relatorios";
import type { ColumnsType } from "antd/es/table";

const ORDEM_FAIXAS = [
  "vencidas",
  "vence_ate_7_dias",
  "vence_8_a_30_dias",
  "vence_apos_30_dias",
] as const;

const ROTULO_FAIXA: Record<(typeof ORDEM_FAIXAS)[number], string> = {
  vencidas: "Vencidas",
  vence_ate_7_dias: "Vence em até 7 dias",
  vence_8_a_30_dias: "Vence em 8 a 30 dias",
  vence_apos_30_dias: "Vence após 30 dias",
};

type LinhaFaixa = {
  key: string;
  faixa: string;
  qtd: number;
  total: string;
};

function useColunasFaixa(): ColumnsType<LinhaFaixa> {
  return useMemo(
    () => [
      { title: "Faixa", dataIndex: "faixa", key: "faixa" },
      { title: "Qtd", dataIndex: "qtd", key: "qtd", align: "right" },
      { title: "Total (R$)", dataIndex: "total", key: "total", align: "right" },
    ],
    [],
  );
}

function linhasFaixa(buckets: RelatorioEnvelhecimentoFinanceiro["pagar"]): LinhaFaixa[] {
  return ORDEM_FAIXAS.map((key) => ({
    key,
    faixa: ROTULO_FAIXA[key],
    qtd: buckets[key]?.quantidade ?? 0,
    total: buckets[key]?.total ?? "0",
  }));
}

function somarFaixas(buckets: RelatorioEnvelhecimentoFinanceiro["pagar"]) {
  return ORDEM_FAIXAS.reduce(
    (acc, key) => {
      const b = buckets[key];
      return {
        qtd: acc.qtd + (b?.quantidade ?? 0),
        total: acc.total + parseFloat(b?.total ?? "0"),
      };
    },
    { qtd: 0, total: 0 },
  );
}

function TabelaFaixas({
  title,
  buckets,
  columns,
}: {
  title: string;
  buckets: RelatorioEnvelhecimentoFinanceiro["pagar"];
  columns: ColumnsType<LinhaFaixa>;
}) {
  return (
    <>
      <Typography.Title level={5} style={{ marginTop: 16 }}>
        {title}
      </Typography.Title>
      <Table<LinhaFaixa>
        rowKey="key"
        columns={columns}
        dataSource={linhasFaixa(buckets)}
        pagination={false}
        size="small"
      />
    </>
  );
}

export function RelatorioEnvelhecimentoPage() {
  const [data, setData] = useState<RelatorioEnvelhecimentoFinanceiro | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const columns = useColunasFaixa();

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const res = await buscarRelatorioEnvelhecimentoFinanceiro();
      setData(res);
    } catch (e) {
      setData(null);
      setErr(e instanceof Error ? e.message : "Erro ao gerar");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const exportar = async (formato: FormatoExportacao) => {
    setExporting(true);
    setErr(null);
    try {
      await exportarRelatorioEnvelhecimentoFinanceiro(formato);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao exportar");
    } finally {
      setExporting(false);
    }
  };

  const totaisPagar = data ? somarFaixas(data.pagar) : null;
  const totaisReceber = data ? somarFaixas(data.receber) : null;

  return (
    <LayoutRelatorio
      titulo="Envelhecimento de títulos"
      descricao="Contas a pagar e a receber em aberto, agrupadas por faixa em relação à data base."
      periodo={data ? `Data base: ${data.hoje}` : undefined}
      onAtualizar={() => void load()}
      onExportarFormato={exportar}
      loadingAtualizar={loading}
      loadingExportar={exporting}
      textoAtualizar="Atualizar prévia"
      erro={err}
    >
      <Spin spinning={loading && !data}>
        {data && totaisPagar && totaisReceber ? (
          <>
            <ResumoRelatorio
              itens={[
                {
                  key: "pagar-qtd",
                  titulo: "Títulos a pagar",
                  valor: totaisPagar.qtd,
                },
                {
                  key: "pagar-total",
                  titulo: "Total a pagar",
                  valor: totaisPagar.total.toFixed(2),
                  prefixo: "R$ ",
                },
                {
                  key: "receber-qtd",
                  titulo: "Títulos a receber",
                  valor: totaisReceber.qtd,
                },
                {
                  key: "receber-total",
                  titulo: "Total a receber",
                  valor: totaisReceber.total.toFixed(2),
                  prefixo: "R$ ",
                },
              ]}
            />
            <TabelaFaixas title="Contas a pagar (em aberto)" buckets={data.pagar} columns={columns} />
            <TabelaFaixas
              title="Contas a receber (em aberto)"
              buckets={data.receber}
              columns={columns}
            />
          </>
        ) : null}
      </Spin>
    </LayoutRelatorio>
  );
}
