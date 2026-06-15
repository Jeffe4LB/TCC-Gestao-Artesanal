import { Button, Typography } from "antd";
import { Link } from "react-router-dom";
import heroInicio from "../assets/inicio-floresta.png";

/** Página inicial pública (sem login) */
export function PublicInicioPage() {
  return (
    <div className="public-home-hero">
      <img
        src={heroInicio}
        alt="Produto artesanal — bem-vindo ao sistema"
        className="home-welcome-photo"
      />
      <div className="home-welcome-overlay home-welcome-overlay--splash" />
      <div className="home-welcome-content home-welcome-content--top">
        <Typography.Text className="home-welcome-kicker">Gestão Artesanal</Typography.Text>
        <Typography.Title level={2} className="home-welcome-title">
          Bem-vindo ao nosso sistema
        </Typography.Title>
      </div>
      <div className="public-home-inner public-home-inner--bottom">
        <div className="public-home-actions">
          <Link to="/login">
            <Button type="primary" size="large" block>
              Entrar no sistema
            </Button>
          </Link>
          <Link to="/registro" className="public-home-registro">
            <Button size="large" block>
              Criar conta
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
