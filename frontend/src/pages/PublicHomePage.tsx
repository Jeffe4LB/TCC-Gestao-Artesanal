import { Button, Card, Typography } from "antd";
import { Link } from "react-router-dom";

/** Página inicial pública (sem login) */
export function PublicHomePage() {
  return (
    <div className="public-home">
      <Card style={{ maxWidth: 480, margin: "0 auto" }}>
        <Typography.Title level={2} style={{ marginTop: 0 }}>
          Gestão Artesanal
        </Typography.Title>
        <Typography.Paragraph type="secondary">
          Acesse o painel para gerenciar cadastros, estoque e financeiro.
        </Typography.Paragraph>
        <Link to="/login">
          <Button type="primary" size="large" block>
            Entrar no sistema
          </Button>
        </Link>
        <Link to="/registro" style={{ display: "block", marginTop: 12 }}>
          <Button size="large" block>
            Criar conta
          </Button>
        </Link>
      </Card>
    </div>
  );
}
