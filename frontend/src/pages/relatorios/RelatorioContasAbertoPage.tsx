import { useCallback, useEffect, useMemo, useState } from "react";
import { Spin, Table, Typography } from "antd";
import {
  buscarRelatorioFinanceiroEmAberto,
  exportarRelatorioFinanceiroEmAberto,
} from "../../api/relatorios";
import { LayoutRelatorio } from "../../components/relatorios/LayoutRelatorio";
import { ResumoRelatorio } from "../../components/relatorios/ResumoRelatorio";
import type {
  FormatoExportacao,
  LinhaContaPagarAberta,
  LinhaContaReceberAberta,
  RelatorioFinanceiroEmAberto,
} from "../../types/relatorios";
import type { ColumnsType } from "antd/es/table";

export function RelatorioContasAbertoPage() {
  const [data, setData] = useState<RelatorioFinanceiroEmAberto | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const res = await buscarRelatorioFinanceiroEmAberto();
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
      await exportarRelatorioFinanceiroEmAberto(formato);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao exportar");
    } finally {
      setExporting(false);
    }
  };

  const payableCols: ColumnsType<LinhaContaPagarAberta> = useMemo(
    () => [
      { title: "Cód.", dataIndex: "id", key: "id", width: 72 },
      { title: "Descrição", dataIndex: "descricao", key: "descricao" },
      { title: "Valor", dataIndex: "valor", key: "valor", align: "right" },
      { title: "Vencimento", dataIndex: "vencimento", key: "vencimento", className: "celula-data-iso" },
      { title: "Fornecedor", dataIndex: "fornecedor", key: "fornecedor", render: (v) => v ?? "—" },
    ],
    [],
  );

  const receivableCols: ColumnsType<LinhaContaReceberAberta> = useMemo(
    () => [
      { title: "Cód.", dataIndex: "id", key: "id", width: 72 },
      { title: "Descrição", dataIndex: "descricao", key: "descricao" },
      { title: "Valor", dataIndex: "valor", key: "valor", align: "right" },
      { title: "Vencimento", dataIndex: "vencimento", key: "vencimento", className: "celula-data-iso" },
      { title: "Cliente", dataIndex: "cliente", key: "cliente", render: (v) => v ?? "—" },
    ],
    [],
  );

  return (
    <LayoutRelatorio
      titulo="Contas em aberto"
      descricao="Títulos com status em aberto, ordenados por vencimento."
      onAtualizar={() => void load()}
      onExportarFormato={exportar}
      loadingAtualizar={loading}
      loadingExportar={exporting}
      textoAtualizar="Atualizar prévia"
      erro={err}
    >
      <Spin spinning={loading && !data}>
        {data ? (
          <>
            <ResumoRelatorio
              itens={[
                {
                  key: "pagar",
                  titulo: "A pagar",
                  valor: data.resumo.total_pagar,
                  prefixo: "R$ ",
                  sufixo: ` (${data.resumo.contagem_pagar})`,
                },
                {
                  key: "receber",
                  titulo: "A receber",
                  valor: data.resumo.total_receber,
                  prefixo: "R$ ",
                  sufixo: ` (${data.resumo.contagem_receber})`,
                },
                {
                  key: "liquido",
                  titulo: "Saldo líquido",
                  valor: data.resumo.saldo_liquido,
                  prefixo: "R$ ",
                },
              ]}
            />

            <Typography.Title level={5} style={{ marginTop: 8 }}>
              Contas a pagar
            </Typography.Title>
            <Table<LinhaContaPagarAberta>
              rowKey="id"
              columns={payableCols}
              dataSource={data.contas_pagar}
              pagination={false}
              size="small"
              scroll={{ x: "max-content" }}
            />

            <Typography.Title level={5} style={{ marginTop: 24 }}>
              Contas a receber
            </Typography.Title>
            <Table<LinhaContaReceberAberta>
              rowKey="id"
              columns={receivableCols}
              dataSource={data.contas_receber}
              pagination={false}
              size="small"
              scroll={{ x: "max-content" }}
            />
          </>
        ) : null}
      </Spin>
    </LayoutRelatorio>
  );
}
