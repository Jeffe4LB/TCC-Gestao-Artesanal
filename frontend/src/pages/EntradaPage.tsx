import { Alert, Button, Card, Form, Input, Spin, Typography } from "antd";
import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { useAutenticacao } from "../hooks/useAutenticacao";

export function EntradaPage() {
  const { isAuthenticated, loading, login, user } = useAutenticacao();
  const navigate = useNavigate();
  const location = useLocation();
  const from =
    (location.state as { from?: { pathname: string } })?.from?.pathname ?? "/app";
  const state = location.state as {
    registered?: boolean;
    passwordReset?: boolean;
  } | null;

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (loading) {
    return (
      <div className="loading-screen">
        <Spin tip="Carregando sessão…" />
      </div>
    );
  }

  if (isAuthenticated) {
    if (user?.senha_temporaria) {
      return <Navigate to="/app/troca-senha-obrigatoria" replace />;
    }
    return <Navigate to={from} replace />;
  }

  return (
    <div className="auth-page">
      <Card className="auth-card" title="Entrar">
        <Typography.Paragraph type="secondary" style={{ marginTop: 0 }}>
          Gestão Artesanal
        </Typography.Paragraph>
        {state?.registered ? (
          <Alert
            type="success"
            message="Conta criada com sucesso. Entre com seu usuário e senha."
            showIcon
            style={{ marginBottom: 16 }}
          />
        ) : null}
        {state?.passwordReset ? (
          <Alert
            type="success"
            message="Senha alterada. Entre com sua nova senha."
            showIcon
            style={{ marginBottom: 16 }}
          />
        ) : null}
        <Form
          layout="vertical"
          onFinish={async (values: { username: string; password: string }) => {
            setError(null);
            setSubmitting(true);
            try {
              const me = await login(values.username, values.password);
              if (me?.senha_temporaria) {
                navigate("/app/troca-senha-obrigatoria", { replace: true });
              } else {
                navigate(from, { replace: true });
              }
            } catch (err) {
              setError(err instanceof Error ? err.message : "Falha no login");
            } finally {
              setSubmitting(false);
            }
          }}
        >
          <Form.Item
            label="Usuário"
            name="username"
            rules={[{ required: true, message: "Informe o usuário" }]}
          >
            <Input autoComplete="username" />
          </Form.Item>
          <Form.Item
            label="Senha"
            name="password"
            rules={[{ required: true, message: "Informe a senha" }]}
          >
            <Input.Password autoComplete="current-password" />
          </Form.Item>
          {error ? (
            <Alert type="error" message={error} showIcon style={{ marginBottom: 16 }} />
          ) : null}
          <Form.Item>
            <Button type="primary" htmlType="submit" block loading={submitting}>
              Entrar
            </Button>
          </Form.Item>
        </Form>
        <Typography.Paragraph style={{ marginBottom: 8 }}>
          <Link to="/recuperar-senha">Esqueci minha senha</Link>
          {" · "}
          <Link to="/registro">Criar conta</Link>
        </Typography.Paragraph>
        <Typography.Text type="secondary" className="small">
          <Link to="/">Voltar ao início</Link>
        </Typography.Text>
      </Card>
    </div>
  );
}
