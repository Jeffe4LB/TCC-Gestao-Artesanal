import { Card, Col, Row, Typography } from "antd";
import { Link } from "react-router-dom";

const cards = [
  {
    to: "/app/relatorios/estoque/posicao",
    title: "Posição de estoque",
    desc: "Saldos por produto, categoria e alerta de mínimo.",
  },
  {
    to: "/app/relatorios/estoque/movimentos",
    title: "Movimentações de estoque",
    desc: "Lançamentos por período (data do movimento).",
  },
  {
    to: "/app/relatorios/estoque/abaixo-minimo",
    title: "Estoque abaixo do mínimo",
    desc: "Mesma regra dos alertas de estoque.",
  },
  {
    to: "/app/relatorios/financeiro/em-aberto",
    title: "Contas em aberto",
    desc: "A pagar e a receber com totais.",
  },
  {
    to: "/app/relatorios/financeiro/fluxo",
    title: "Fluxo de caixa (período)",
    desc: "Entradas e saídas pela data efetiva (pago/recebido).",
  },
  {
    to: "/app/relatorios/financeiro/envelhecimento",
    title: "Envelhecimento",
    desc: "Faixas de vencimento para títulos em aberto.",
  },
  {
    to: "/app/relatorios/financeiro/receita-produto",
    title: "Receita por produto",
    desc: "Faturamento e margem a partir das linhas de contas a receber (data de emissão).",
  },
];

export function ReportsHomePage() {
  return (
    <div>
      <Typography.Title level={3}>Relatórios</Typography.Title>
      <Row gutter={[16, 16]}>
        {cards.map((c) => (
          <Col xs={24} sm={12} lg={8} key={c.to}>
            <Link to={c.to}>
              <Card hoverable title={c.title}>
                <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
                  {c.desc}
                </Typography.Paragraph>
              </Card>
            </Link>
          </Col>
        ))}
      </Row>
    </div>
  );
}
