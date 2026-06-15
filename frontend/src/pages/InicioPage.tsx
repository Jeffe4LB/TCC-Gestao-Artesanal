import { Typography } from "antd";
import { Link } from "react-router-dom";
import heroInicio from "../assets/inicio-floresta.png";

/**
 * Boas-vindas após o login — arte em tela cheia. Dados e alertas ficam no Painel.
 */
export function InicioPage() {
  return (
    <div className="home-welcome">
      <div className="home-welcome-hero home-welcome-hero--splash">
        <img
          src={heroInicio}
          alt="Produto artesanal — bem-vindo"
          className="home-welcome-photo"
        />
        <div className="home-welcome-overlay home-welcome-overlay--splash" />
        <div className="home-welcome-content home-welcome-content--top">
          <Typography.Text className="home-welcome-kicker">Gestão Artesanal</Typography.Text>
          <Typography.Title level={1} className="home-welcome-title">
            Bem-vindo
          </Typography.Title>
        </div>
        <div className="home-welcome-content home-welcome-content--bottom">
          <Link to="/app/dashboard" className="home-welcome-cta">
            Ir ao painel
          </Link>
        </div>
      </div>
    </div>
  );
}
