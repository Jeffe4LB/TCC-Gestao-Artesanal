import { Button, Table, Tag } from "antd";
import type { ColumnsType } from "antd/es/table";
import type { ParcelaDocumento, SituacaoPagar, SituacaoReceber } from "../../types/financeiro";

const ROTULO_SITUACAO: Record<string, string> = {
  aberto: "Em aberto",
  parcial: "Parcial",
  pago: "Pago",
  recebido: "Recebido",
  cancelado: "Cancelado",
};

const COR_SITUACAO: Record<string, string> = {
  aberto: "processing",
  parcial: "warning",
  pago: "success",
  recebido: "success",
  cancelado: "default",
};

type Props = {
  parcelas: ParcelaDocumento[];
  tipo: "pagar" | "receber";
  documentoCancelado?: boolean;
  onQuitar?: (parcela: ParcelaDocumento) => void;
};

export function TabelaParcelas({ parcelas, tipo, documentoCancelado, onQuitar }: Props) {
  const columns: ColumnsType<ParcelaDocumento> = [
    {
      title: "Parcela",
      key: "parcela",
      width: 90,
      render: (_, row) => `${row.numero_parcela}/${row.total_parcelas}`,
    },
    { title: "Vencimento", dataIndex: "vencimento", key: "vencimento", width: 120 },
    { title: "Descrição", dataIndex: "descricao", key: "descricao" },
    { title: "Valor", dataIndex: "valor", key: "valor", width: 100 },
    { title: "Pago", dataIndex: "valor_pago", key: "valor_pago", width: 100 },
    { title: "Saldo", dataIndex: "saldo_restante", key: "saldo_restante", width: 100 },
    {
      title: "Situação",
      dataIndex: "situacao",
      key: "situacao",
      width: 120,
      render: (s: SituacaoPagar | SituacaoReceber) => (
        <Tag color={COR_SITUACAO[s] ?? "default"}>{ROTULO_SITUACAO[s] ?? s}</Tag>
      ),
    },
    {
      title: "Ações",
      key: "acoes",
      width: 110,
      render: (_, row) => {
        const quitada = row.situacao === "pago" || row.situacao === "recebido";
        const cancelada = row.situacao === "cancelado";
        if (!onQuitar || quitada || cancelada || documentoCancelado) return "—";
        return (
          <Button size="small" type="link" onClick={() => onQuitar(row)}>
            {tipo === "pagar" ? "Baixar" : "Receber"}
          </Button>
        );
      },
    },
  ];

  return (
    <Table
      rowKey="id"
      size="small"
      pagination={false}
      columns={columns}
      dataSource={parcelas}
    />
  );
}
