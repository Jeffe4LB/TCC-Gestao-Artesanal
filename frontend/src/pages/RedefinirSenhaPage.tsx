import { Alert, Button, Card, Form, Input, Spin, Typography } from "antd";
import { useState } from "react";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom";
import { confirmPasswordReset } from "../api/autenticacaoPublica";
import { useAutenticacao } from "../hooks/useAutenticacao";

export function RedefinirSenhaPage() {
  const { isAuthenticated, loading } = useAutenticacao();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const uid = searchParams.get("uid") ?? "";
  const token = searchParams.get("token") ?? "";

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

  const linkInvalid = !uid || !token;

  return (
    <div className="auth-page">
      <Card className="auth-card" title="Nova senha">
        <Typography.Paragraph type="secondary" style={{ marginTop: 0 }}>
          Defina uma nova senha para sua conta.
        </Typography.Paragraph>
        {linkInvalid ? (
          <Alert
            type="warning"
            showIcon
            message="Link incompleto"
            description={
              <>
                Abra o link enviado por e-mail ou solicite um novo em{" "}
                <Link to="/recuperar-senha">recuperar senha</Link>.
              </>
            }
            style={{ marginBottom: 16 }}
          />
        ) : (
          <Form
            layout="vertical"
            onFinish={async (values: {
              new_password: string;
              new_password_confirm: string;
            }) => {
              setError(null);
              setSubmitting(true);
              try {
                await confirmPasswordReset({
                  uid,
                  token,
                  new_password: values.new_password,
                  new_password_confirm: values.new_password_confirm,
                });
                navigate("/login", { replace: true, state: { passwordReset: true } });
              } catch (err) {
                setError(
                  err instanceof Error ? err.message : "Não foi possível alterar a senha",
                );
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
                { required: true, message: "Confirme a senha" },
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
                Salvar nova senha
              </Button>
            </Form.Item>
          </Form>
        )}
        <Typography.Paragraph style={{ marginBottom: 8 }}>
          <Link to="/login">Voltar ao login</Link>
        </Typography.Paragraph>
      </Card>
    </div>
  );
}
