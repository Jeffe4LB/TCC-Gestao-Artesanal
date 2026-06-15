import { Alert, Button, Card, Collapse, Space, Typography } from "antd";
import type { ReactNode } from "react";
import type { FormatoExportacao } from "../../types/relatorios";
import { BotoesExportacao } from "./BotoesExportacao";

type Props = {
  titulo: string;
  descricao?: string;
  periodo?: string;
  filtros?: ReactNode;
  onAtualizar?: () => void;
  /**
   * Handler de exportação multi-formato. Quando fornecido, exibe o
   * `BotoesExportacao` (CSV/PDF/XLSX). Preferir esta prop em telas novas.
   */
  onExportarFormato?: (formato: FormatoExportacao) => void | Promise<void>;
  /**
   * Handler legado: exibe um botão único "Exportar CSV". Mantido para
   * compatibilidade até que todas as páginas migrem para `onExportarFormato`.
   */
  onExportar?: () => void;
  loadingAtualizar?: boolean;
  loadingExportar?: boolean;
  textoAtualizar?: string;
  erro?: string | null;
  children?: ReactNode;
};

export function LayoutRelatorio({
  titulo,
  descricao,
  periodo,
  filtros,
  onAtualizar,
  onExportarFormato,
  onExportar,
  loadingAtualizar,
  loadingExportar,
  textoAtualizar = "Atualizar",
  erro,
  children,
}: Props) {
  const temAcoes = !!(onAtualizar || onExportarFormato || onExportar);
  const acoes = temAcoes ? (
    <Space wrap>
      {onAtualizar ? (
        <Button onClick={onAtualizar} loading={loadingAtualizar}>
          {textoAtualizar}
        </Button>
      ) : null}
      {onExportarFormato ? (
        <BotoesExportacao
          onExportar={onExportarFormato}
          loading={loadingExportar}
        />
      ) : onExportar ? (
        <Button type="primary" onClick={onExportar} loading={loadingExportar}>
          Exportar CSV
        </Button>
      ) : null}
    </Space>
  ) : null;

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <div>
        <Typography.Title level={4} style={{ margin: 0 }}>
          {titulo}
        </Typography.Title>
        {descricao ? (
          <Typography.Paragraph type="secondary" style={{ marginTop: 8, marginBottom: 0 }}>
            {descricao}
          </Typography.Paragraph>
        ) : null}
        {periodo ? (
          <Typography.Text type="secondary" style={{ display: "block", marginTop: 8 }}>
            {periodo}
          </Typography.Text>
        ) : null}
      </div>

      {filtros ? (
        <>
          <div className="relatorio-filtros-desktop">
            <Card size="small" title="Filtros">
              {filtros}
            </Card>
          </div>
          <div className="relatorio-filtros-mobile">
            <Collapse
              size="small"
              items={[{ key: "filtros", label: "Filtros", children: filtros }]}
            />
          </div>
        </>
      ) : null}

      {acoes}

      {erro ? <Alert type="error" message={erro} showIcon /> : null}

      {children}
    </Space>
  );
}
