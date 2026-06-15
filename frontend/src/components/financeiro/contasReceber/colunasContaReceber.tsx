import { Link } from "react-router-dom";
import { Button, Popconfirm, Space, Tooltip } from "antd";
import { DeleteOutlined, EditOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import type { ContaReceber, SituacaoReceber } from "../../../types/financeiro";
import { COLUNA_DATA_ISO } from "./helpers";

const STATUS_LABEL: Record<SituacaoReceber, string> = {
  aberto: "Em aberto",
  parcial: "Parcial",
  recebido: "Recebido",
  cancelado: "Cancelado",
};

export function colunasContaReceber(handlers: {
  onEdit: (row: ContaReceber) => void;
  onDelete: (row: ContaReceber) => void;
}): ColumnsType<ContaReceber> {
  return [
    {
      title: "Emissão",
      dataIndex: "data_emissao",
      key: "data_emissao",
      ...COLUNA_DATA_ISO,
    },
    {
      title: "Vencimento",
      dataIndex: "vencimento",
      key: "vencimento",
      ...COLUNA_DATA_ISO,
    },
    { title: "Descrição", dataIndex: "descricao", key: "descricao" },
    { title: "Cliente", dataIndex: "nome_cliente", key: "nome_cliente", render: (v) => v ?? "—" },
    {
      title: "Linhas",
      key: "nlines",
      width: 72,
      render: (_: unknown, r: ContaReceber) => r.linhas?.length ?? 0,
    },
    { title: "Total R$", dataIndex: "valor", key: "valor", width: 100 },
    {
      title: "Parcela",
      key: "parcela",
      width: 90,
      render: (_, row) =>
        row.rotulo_parcela ? (
          <Link to="/app/financeiro/documentos">{row.rotulo_parcela}</Link>
        ) : (
          "—"
        ),
    },
    {
      title: "Status",
      dataIndex: "situacao",
      key: "situacao",
      width: 110,
      render: (s: SituacaoReceber) => STATUS_LABEL[s],
    },
    {
      title: "Recebido em",
      dataIndex: "recebido_em",
      key: "recebido_em",
      ...COLUNA_DATA_ISO,
      render: (v: string | null | undefined) => v ?? "—",
    },
    {
      title: "Ações",
      key: "actions",
      width: 96,
      render: (_, row) => (
        <Space size={4}>
          <Tooltip title="Editar">
            <Button
              type="text"
              icon={<EditOutlined />}
              aria-label="Editar"
              onClick={() => handlers.onEdit(row)}
            />
          </Tooltip>
          <Tooltip title="Excluir">
            <Popconfirm
              title={`Excluir "${row.descricao}"?`}
              okText="Excluir"
              cancelText="Cancelar"
              okButtonProps={{ danger: true }}
              onConfirm={() => handlers.onDelete(row)}
            >
              <Button type="text" danger icon={<DeleteOutlined />} aria-label="Excluir" />
            </Popconfirm>
          </Tooltip>
        </Space>
      ),
    },
  ];
}
