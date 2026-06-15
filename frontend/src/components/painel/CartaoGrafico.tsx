import type { ReactNode } from "react";
import { Card, Empty, Spin, Typography } from "antd";

type Props = {
  titulo: string;
  descricao?: string;
  /** Conteúdo do gráfico em si (children). */
  children: ReactNode;
  /** Mostra spinner sobreposto. */
  carregando?: boolean;
  /** Considera vazio (mostra `Empty` em vez do children). */
  vazio?: boolean;
  /** Mensagem custom para o estado vazio. */
  textoVazio?: string;
  /** Slot opcional no canto direito do header (ex.: select de período). */
  extra?: ReactNode;
  /** Altura mínima útil para evitar layout shift quando o gráfico ainda carrega. */
  alturaMinima?: number;
};

/**
 * Wrapper reutilizável para os gráficos do painel — padroniza Card + Spin +
 * Empty e isola a parte visual dos componentes de gráfico (cada gráfico foca
 * só na própria renderização).
 */
export function CartaoGrafico({
  titulo,
  descricao,
  children,
  carregando = false,
  vazio = false,
  textoVazio = "Nada para mostrar no período",
  extra,
  alturaMinima = 280,
}: Props) {
  return (
    <Card
      title={titulo}
      extra={extra}
      styles={{ body: { paddingTop: 12 } }}
    >
      {descricao ? (
        <Typography.Paragraph type="secondary" style={{ marginTop: 0, marginBottom: 12 }}>
          {descricao}
        </Typography.Paragraph>
      ) : null}
      <Spin spinning={carregando}>
        <div style={{ minHeight: alturaMinima }}>
          {vazio ? (
            <Empty description={textoVazio} style={{ paddingTop: 32 }} />
          ) : (
            children
          )}
        </div>
      </Spin>
    </Card>
  );
}
