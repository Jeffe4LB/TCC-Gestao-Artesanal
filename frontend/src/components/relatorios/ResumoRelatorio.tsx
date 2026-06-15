import { Card, Col, Row, Statistic } from "antd";

export type ItemResumoRelatorio = {
  key: string;
  titulo: string;
  valor: string | number;
  prefixo?: string;
  sufixo?: string;
};

export function ResumoRelatorio({ itens }: { itens: ItemResumoRelatorio[] }) {
  if (!itens.length) return null;

  return (
    <Card size="small" title="Resumo" style={{ marginBottom: 16 }}>
      <Row gutter={[16, 16]}>
        {itens.map((item) => (
          <Col xs={24} sm={12} md={6} key={item.key}>
            <Statistic
              title={item.titulo}
              value={item.valor}
              prefix={item.prefixo}
              suffix={item.sufixo}
            />
          </Col>
        ))}
      </Row>
    </Card>
  );
}
