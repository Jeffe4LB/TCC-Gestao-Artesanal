import { Alert, Button, Card, Form, Input, Spin, Typography } from "antd";
import { useState } from "react";
import { Navigate } from "react-router-dom";
import { trocarSenhaInicial } from "../api/trocarSenhaInicial";
import { useAutenticacao } from "../hooks/useAutenticacao";

export function TrocaSenhaObrigatoriaPage() {
  const { user, loading, refreshUser } = useAutenticacao();
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  if (loading) {
    return (
      <div className="loading-screen">
        <Spin tip="Carregando sessão…" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (!user.senha_temporaria || done) {
    return <Navigate to="/app" replace />;
  }

  return (
    <div className="auth-page">
      <Card className="auth-card" title="Defina sua nova senha">
        <Typography.Paragraph type="secondary" style={{ marginTop: 0 }}>
          Por segurança, troque a senha temporária antes de continuar.
        </Typography.Paragraph>
        <Form
          layout="vertical"
          onFinish={async (values: {
            new_password: string;
            new_password_confirm: string;
          }) => {
            setError(null);
            setSubmitting(true);
            try {
              await trocarSenhaInicial({
                new_password: values.new_password,
                new_password_confirm: values.new_password_confirm,
              });
              await refreshUser();
              setDone(true);
            } catch (err) {
              setError(err instanceof Error ? err.message : "Não foi possível alterar a senha");
            } finally {
              setSubmitting(false);
            }
          }}
        >
          <Form.Item
            label="Nova senha"
            name="new_password"
            rules={[
              { required: true, message: "Informe a nova senha" },
              { min: 8, message: "Mínimo de 8 caracteres" },
            ]}
          >
            <Input.Password autoComplete="new-password" />
          </Form.Item>
          <Form.Item
            label="Confirmar nova senha"
            name="new_password_confirm"
            dependencies={["new_password"]}
            rules={[
              { required: true, message: "Confirme a nova senha" },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue("new_password") === value) {
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
              Salvar e continuar
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
