import {
  ArrowRightOutlined,
  ExportOutlined,
  HistoryOutlined,
  ShoppingOutlined,
  ToolOutlined,
} from "@ant-design/icons";
import { Button, Card, Col, Row, Space, Table, Typography } from "antd";
import type { ColumnsType } from "antd/es/table";
import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { rotuloTipoMovimentacao } from "../../constants/tiposMovimentacaoEstoque";
import { useAutenticacao } from "../../hooks/useAutenticacao";

type FluxoSaida = {
  key: string;
  titulo: string;
  descricao: string;
  to: string;
  icon: ReactNode;
  capacidade: "financeiro" | "receitas_producao" | "estoque_movimentacoes";
};

const FLUXOS: FluxoSaida[] = [
  {
    key: "venda",
    titulo: "Venda / entrega ao cliente",
    descricao:
      "Ao incluir produtos nas linhas da conta a receber, o sistema registra movimento venda e reduz o saldo automaticamente.",
    to: "/app/financeiro/receber",
    icon: <ShoppingOutlined />,
    capacidade: "financeiro",
  },
  {
    key: "producao",
    titulo: "Consumo na produção",
    descricao:
      "Ao executar uma ordem de produção, os insumos da receita são baixados no consumo da produçao, e o produto acabado entra no estoque.",
    to: "/app/estoque/producao",
    icon: <ToolOutlined />,
    capacidade: "receitas_producao",
  },
  {
    key: "ajuste",
    titulo: "Ajuste manual (perda, quebra, amostra)",
    descricao:
      "Em Movimentos, use o tipo ajuste com quantidade negativa para registrar saídas que não passam por venda ou produção.",
    to: "/app/estoque/movimentos",
    icon: <ExportOutlined />,
    capacidade: "estoque_movimentacoes",
  },
];

type TipoMovimentoSaida = {
  codigo: string;
  efeito: string;
  fluxo: string;
};

const TIPOS_SAIDA: TipoMovimentoSaida[] = [
  {
    codigo: "venda_receber",
    efeito: "Reduz saldo",
    fluxo: "Contas a receber (linhas com produto)",
  },
  {
    codigo: "consumo_producao",
    efeito: "Reduz saldo (insumos)",
    fluxo: "Ordem de produção",
  },
  {
    codigo: "ajuste",
    efeito: "Reduz ou aumenta saldo",
    fluxo: "Movimentos (quantidade negativa = saída)",
  },
  {
    codigo: "estorno_venda_receber",
    efeito: "Devolve saldo (estorno)",
    fluxo: "Cancelamento ou edição de conta a receber",
  },
  {
    codigo: "estorno_entrada_producao",
    efeito: "Remove saldo do acabado (estorno)",
    fluxo: "Cancelamento de produção",
  },
  {
    codigo: "estorno_consumo_producao",
    efeito: "Devolve insumos (estorno)",
    fluxo: "Cancelamento de produção",
  },
];

export function SaidasEstoquePage() {
  const { user } = useAutenticacao();
  const cap = user?.capacidades;

  const columns: ColumnsType<TipoMovimentoSaida> = [
    {
      title: "Tipo",
      dataIndex: "codigo",
      key: "codigo",
      render: (codigo: string) => rotuloTipoMovimentacao(codigo),
    },
    { title: "Efeito no saldo", dataIndex: "efeito", key: "efeito" },
    { title: "Onde ocorre", dataIndex: "fluxo", key: "fluxo" },
  ];

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <div>
        <Typography.Title level={3} style={{ margin: 0 }}>
          Saídas de estoque
        </Typography.Title>
      </div>

      <Row gutter={[16, 16]}>
        {FLUXOS.map((fluxo) => {
          const permitido = cap?.[fluxo.capacidade] ?? false;
          return (
            <Col xs={24} md={8} key={fluxo.key}>
              <Card
                size="small"
                title={
                  <Space>
                    {fluxo.icon}
                    {fluxo.titulo}
                  </Space>
                }
                style={{ height: "100%" }}
              >
                <Typography.Paragraph style={{ minHeight: 72 }}>{fluxo.descricao}</Typography.Paragraph>
                {permitido ? (
                  <Link to={fluxo.to}>
                    <Button type="primary" icon={<ArrowRightOutlined />}>
                      Ir para o fluxo
                    </Button>
                  </Link>
                ) : (
                  <Typography.Text type="secondary">
                    Você não tem permissão para acessar este fluxo.
                  </Typography.Text>
                )}
              </Card>
            </Col>
          );
        })}
      </Row>

      <Card
        size="small"
        title="Tipos de movimentação relacionados à saída"
        extra={
          cap?.estoque_movimentacoes || cap?.estoque_leitura ? (
            <Link to="/app/estoque/movimentos">
              <Button type="link" icon={<HistoryOutlined />}>
                Ver histórico em Movimentos
              </Button>
            </Link>
          ) : null
        }
      >
        <Table<TipoMovimentoSaida>
          rowKey="codigo"
          size="small"
          pagination={false}
          columns={columns}
          dataSource={TIPOS_SAIDA}
        />
      </Card>
    </Space>
  );
}
