import { Alert, Button, Card, Form, Input, Spin, Typography } from "antd";
import { useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { requestPasswordReset } from "../api/autenticacaoPublica";
import { useAutenticacao } from "../hooks/useAutenticacao";

export function EsqueciSenhaPage() {
  const { isAuthenticated, loading } = useAutenticacao();
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [devNotice, setDevNotice] = useState<string | null>(null);
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
      <Card className="auth-card" title="Recuperar senha">
        <Typography.Paragraph type="secondary" style={{ marginTop: 0 }}>
          Informe o e-mail da sua conta. Se existir cadastro, enviaremos um link para
          redefinir a senha.
        </Typography.Paragraph>
        <Form
          layout="vertical"
          onFinish={async (values: { email: string }) => {
            setError(null);
            setSuccess(null);
            setDevNotice(null);
            setSubmitting(true);
            try {
              const res = await requestPasswordReset(values.email.trim());
              setSuccess(res.detail);
              if (res.dev_notice) setDevNotice(res.dev_notice);
            } catch (err) {
              setError(err instanceof Error ? err.message : "Não foi possível enviar");
            } finally {
              setSubmitting(false);
            }
          }}
        >
          <Form.Item
            label="E-mail"
            name="email"
            rules={[
              { required: true, message: "Informe o e-mail" },
              { type: "email", message: "E-mail inválido" },
            ]}
          >
            <Input autoComplete="email" />
          </Form.Item>
          {error ? (
            <Alert type="error" message={error} showIcon style={{ marginBottom: 16 }} />
          ) : null}
          {success ? (
            <Alert type="success" message={success} showIcon style={{ marginBottom: 16 }} />
          ) : null}
          {devNotice ? (
            <Alert type="warning" message={devNotice} showIcon style={{ marginBottom: 16 }} />
          ) : null}
          <Form.Item>
            <Button type="primary" htmlType="submit" block loading={submitting}>
              Enviar instruções
            </Button>
          </Form.Item>
        </Form>
        <Typography.Paragraph style={{ marginBottom: 8 }}>
          <Link to="/login">Voltar ao login</Link>
        </Typography.Paragraph>
        <Typography.Text type="secondary" className="small">
          <Link to="/">Início</Link>
        </Typography.Text>
      </Card>
    </div>
  );
}
