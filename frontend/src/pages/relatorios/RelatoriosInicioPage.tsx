import { Card, Col, Row, Typography } from "antd";
import {
  AlertOutlined,
  BarChartOutlined,
  ClockCircleOutlined,
  DollarOutlined,
  InboxOutlined,
  SwapOutlined,
  WalletOutlined,
} from "@ant-design/icons";
import { Link } from "react-router-dom";
import type { ReactNode } from "react";

type CardRelatorio = {
  to: string;
  title: string;
  desc: string;
  icon: ReactNode;
};

const grupos: { titulo: string; cards: CardRelatorio[] }[] = [
  {
    titulo: "Estoque",
    cards: [
      {
        to: "/app/relatorios/estoque/posicao",
        title: "Posição de estoque",
        desc: "Saldos por produto, valor estimado e alerta de mínimo.",
        icon: <InboxOutlined />,
      },
      {
        to: "/app/relatorios/estoque/movimentos",
        title: "Movimentações de estoque",
        desc: "Lançamentos por período com totais por tipo de movimento.",
        icon: <SwapOutlined />,
      },
      {
        to: "/app/relatorios/estoque/abaixo-minimo",
        title: "Estoque abaixo do mínimo",
        desc: "Mesma regra dos alertas de estoque.",
        icon: <AlertOutlined />,
      },
    ],
  },
  {
    titulo: "Financeiro",
    cards: [
      {
        to: "/app/relatorios/financeiro/em-aberto",
        title: "Contas em aberto",
        desc: "A pagar e a receber com totais e saldo líquido.",
        icon: <WalletOutlined />,
      },
      {
        to: "/app/relatorios/financeiro/fluxo",
        title: "Fluxo de caixa (período)",
        desc: "Entradas e saídas pela data efetiva (pago/recebido).",
        icon: <DollarOutlined />,
      },
      {
        to: "/app/relatorios/financeiro/envelhecimento",
        title: "Envelhecimento",
        desc: "Faixas de vencimento para títulos em aberto.",
        icon: <ClockCircleOutlined />,
      },
      {
        to: "/app/relatorios/financeiro/receita-produto",
        title: "Receita por produto",
        desc: "Faturamento, custo, lucro e margem por produto (data de emissão).",
        icon: <BarChartOutlined />,
      },
    ],
  },
];

export function RelatoriosInicioPage() {
  return (
    <div>
      <Typography.Title level={3}>Relatórios</Typography.Title>
      <Typography.Paragraph type="secondary">
        Consultas consolidadas de estoque e financeiro. Use os filtros em cada relatório e exporte
        CSV quando precisar compartilhar.
      </Typography.Paragraph>

      {grupos.map((grupo) => (
        <section key={grupo.titulo} style={{ marginBottom: 32 }}>
          <Typography.Title level={4} style={{ marginBottom: 16 }}>
            {grupo.titulo}
          </Typography.Title>
          <Row gutter={[16, 16]}>
            {grupo.cards.map((c) => (
              <Col xs={24} sm={12} lg={8} key={c.to}>
                <Link to={c.to} style={{ color: "inherit" }}>
                  <Card hoverable>
                    <SpaceCard icon={c.icon} title={c.title} desc={c.desc} />
                  </Card>
                </Link>
              </Col>
            ))}
          </Row>
        </section>
      ))}
    </div>
  );
}

function SpaceCard({
  icon,
  title,
  desc,
}: {
  icon: ReactNode;
  title: string;
  desc: string;
}) {
  return (
    <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
      <span style={{ fontSize: 22, color: "#2563eb", lineHeight: 1 }}>{icon}</span>
      <div>
        <Typography.Text strong style={{ display: "block", marginBottom: 4 }}>
          {title}
        </Typography.Text>
        <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
          {desc}
        </Typography.Paragraph>
      </div>
    </div>
  );
}
