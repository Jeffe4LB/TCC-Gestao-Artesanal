import { useCallback, useEffect, useMemo, useState } from "react";
import { Alert, Col, Drawer, Row, Spin, Statistic, Table, Tag } from "antd";
import type { ColumnsType } from "antd/es/table";
import { Link } from "react-router-dom";
import { obterHistoricoCliente, obterHistoricoFornecedor } from "../../api/cadastro";
import { BarraPaginacao } from "../BarraPaginacao";
import type {
  HistoricoTituloParceiro,
  SituacaoPagar,
  SituacaoReceber,
} from "../../types/financeiro";
import { formatarBRL } from "../../utils/moeda";

const PAGE_SIZE = 20;

const LABEL_RECEBER: Record<SituacaoReceber, string> = {
  aberto: "Em aberto",
  parcial: "Parcial",
  recebido: "Recebido",
  cancelado: "Cancelado",
};

const LABEL_PAGAR: Record<SituacaoPagar, string> = {
  aberto: "Em aberto",
  parcial: "Parcial",
  pago: "Pago",
  cancelado: "Cancelado",
};

const COR_SITUACAO: Record<string, string> = {
  aberto: "processing",
  parcial: "warning",
  recebido: "success",
  pago: "success",
  cancelado: "default",
};

type HistoricoParceiroDrawerProps = {
  open: boolean;
  onClose: () => void;
  titulo: string;
  tipo: "cliente" | "fornecedor";
  parceiroId: number;
};

export function HistoricoParceiroDrawer({
  open,
  onClose,
  titulo,
  tipo,
  parceiroId,
}: HistoricoParceiroDrawerProps) {
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [resumo, setResumo] = useState<Record<string, string>>({});
  const [list, setList] = useState<HistoricoTituloParceiro[]>([]);
  const [total, setTotal] = useState(0);

  const load = useCallback(async () => {
    if (!open || !parceiroId) return;
    setLoading(true);
    setErr(null);
    try {
      const fetcher = tipo === "cliente" ? obterHistoricoCliente : obterHistoricoFornecedor;
      const data = await fetcher(parceiroId, { page });
      setResumo(data.resumo);
      setList(data.resultados);
      setTotal(data.total);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao carregar histórico");
    } finally {
      setLoading(false);
    }
  }, [open, parceiroId, page, tipo]);

  useEffect(() => {
    if (open) {
      setPage(1);
    }
  }, [open, parceiroId, tipo]);

  useEffect(() => {
    void load();
  }, [load]);

  const resumoCards = useMemo(() => {
    if (tipo === "cliente") {
      return [
        { key: "aberto", label: "Em aberto" },
        { key: "parcial", label: "Parcial" },
        { key: "recebido", label: "Recebido" },
        { key: "cancelado", label: "Cancelado" },
      ];
    }
    return [
      { key: "aberto", label: "Em aberto" },
      { key: "parcial", label: "Parcial" },
      { key: "pago", label: "Pago" },
      { key: "cancelado", label: "Cancelado" },
    ];
  }, [tipo]);

  const columns: ColumnsType<HistoricoTituloParceiro> = useMemo(
    () => [
      { title: "Descrição", dataIndex: "descricao", key: "descricao", ellipsis: true },
      ...(tipo === "cliente"
        ? [
            {
              title: "Emissão",
              dataIndex: "data_emissao",
              key: "data_emissao",
              width: 110,
              className: "celula-data-iso",
            },
          ]
        : []),
      {
        title: "Vencimento",
        dataIndex: "vencimento",
        key: "vencimento",
        width: 110,
        className: "celula-data-iso",
      },
      {
        title: "Valor",
        dataIndex: "valor",
        key: "valor",
        width: 120,
        align: "right",
        render: (v: string) => formatarBRL(v),
      },
      {
        title: "Parcela",
        dataIndex: "rotulo_parcela",
        key: "rotulo_parcela",
        width: 80,
        render: (v: string | null) => v ?? "—",
      },
      {
        title: "Situação",
        dataIndex: "situacao",
        key: "situacao",
        width: 120,
        render: (s: SituacaoPagar | SituacaoReceber) => {
          const label =
            tipo === "cliente"
              ? LABEL_RECEBER[s as SituacaoReceber]
              : LABEL_PAGAR[s as SituacaoPagar];
          return <Tag color={COR_SITUACAO[s] ?? "default"}>{label}</Tag>;
        },
      },
      {
        title: tipo === "cliente" ? "Recebido em" : "Pago em",
        key: "data_quitacao",
        width: 110,
        className: "celula-data-iso",
        render: (_, row) => row.recebido_em ?? row.pago_em ?? "—",
      },
    ],
    [tipo],
  );

  const linkFinanceiro = tipo === "cliente" ? "/app/financeiro/receber" : "/app/financeiro/pagar";

  return (
    <Drawer
      title={`Histórico financeiro — ${titulo}`}
      open={open}
      onClose={onClose}
      width={720}
      destroyOnClose
    >
      <Spin spinning={loading}>
        <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
          {resumoCards.map((card) => (
            <Col xs={12} sm={6} key={card.key}>
              <Statistic
                title={card.label}
                value={formatarBRL(resumo[card.key] ?? "0")}
                valueStyle={{ fontSize: 16 }}
              />
            </Col>
          ))}
        </Row>

        {err ? <Alert type="error" message={err} showIcon style={{ marginBottom: 16 }} /> : null}

        <Table<HistoricoTituloParceiro>
          rowKey="id"
          size="small"
          columns={columns}
          dataSource={list}
          pagination={false}
        />
        <BarraPaginacao page={page} totalCount={total} pageSize={PAGE_SIZE} onPageChange={setPage} />

        <div style={{ marginTop: 16 }}>
          <Link to={linkFinanceiro}>Abrir módulo financeiro</Link>
        </div>
      </Spin>
    </Drawer>
  );
}
