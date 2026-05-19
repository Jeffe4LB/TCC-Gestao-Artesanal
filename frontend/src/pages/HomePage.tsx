import { Typography } from "antd";

/**
 * Boas-vindas após o login — visual leve. Dados e alertas ficam no Dashboard.
 */
export function HomePage() {
  return (
    <div className="home-welcome">
      <div className="home-welcome-hero">
        <div className="home-welcome-overlay" />
        <div className="home-welcome-content">
          <Typography.Text className="home-welcome-kicker">Gestão Artesanal</Typography.Text>
          <Typography.Title level={1} className="home-welcome-title" style={{ color: "#fff" }}>
            Bem-vindo
          </Typography.Title>
        </div>
      </div>
    </div>
  );
}
