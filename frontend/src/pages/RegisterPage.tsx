import { Alert, Button, Card, Form, Input, Spin, Typography } from "antd";
import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { registerUser } from "../api/authPublic";
import { useAuth } from "../hooks/useAuth";

export function RegisterPage() {
  const navigate = useNavigate();
  const { isAuthenticated, loading } = useAuth();
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
    return <Navigate to="/app" replace />;
  }

  return (
    <div className="auth-page">
      <Card className="auth-card" title="Criar conta">
        <Typography.Paragraph type="secondary" style={{ marginTop: 0 }}>
          Gestão Artesanal — cadastro de novo usuário
        </Typography.Paragraph>
        <Form
          layout="vertical"
          onFinish={async (values: {
            username: string;
            email?: string;
            password: string;
            password_confirm: string;
          }) => {
            setError(null);
            setSubmitting(true);
            try {
              const res = await registerUser({
                username: values.username,
                password: values.password,
                email: values.email,
              });
              if (import.meta.env.DEV && res._debug_database) {
                console.info(
                  "[Gestão Artesanal] Conta criada (id=%s). O Django gravou nesta base:\n%s\nConfirme com: python3 manage.py list_auth_users",
                  res.id,
                  res._debug_database,
                );
              }
              navigate("/login", { replace: true, state: { registered: true } });
            } catch (err) {
              setError(err instanceof Error ? err.message : "Falha no cadastro");
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
            label="E-mail"
            name="email"
            extra="Recomendado para recuperação de senha."
            rules={[{ type: "email", message: "E-mail inválido" }]}
          >
            <Input autoComplete="email" />
          </Form.Item>
          <Form.Item
            label="Senha"
            name="password"
            rules={[
              { required: true, message: "Informe a senha" },
              { min: 8, message: "Mínimo de 8 caracteres" },
            ]}
          >
            <Input.Password autoComplete="new-password" />
          </Form.Item>
          <Form.Item
            label="Confirmar senha"
            name="password_confirm"
            dependencies={["password"]}
            rules={[
              { required: true, message: "Confirme a senha" },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue("password") === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error("As senhas não coincidem"));
                },
              }),
            ]}
          >
            <Input.Password autoComplete="new-password" />
          </Form.Item>
          {error ? (
            <Alert type="error" message={error} showIcon style={{ marginBottom: 16 }} />
          ) : null}
          <Form.Item>
            <Button type="primary" htmlType="submit" block loading={submitting}>
              Cadastrar
            </Button>
          </Form.Item>
        </Form>
        <Typography.Paragraph style={{ marginBottom: 8 }}>
          <Link to="/login">Já tenho conta — entrar</Link>
        </Typography.Paragraph>
        <Typography.Text type="secondary" className="small">
          <Link to="/">Voltar ao início</Link>
        </Typography.Text>
      </Card>
    </div>
  );
}
