import { DownloadOutlined } from "@ant-design/icons";
import { Dropdown, type MenuProps } from "antd";
import type { FormatoExportacao } from "../../types/relatorios";
import { ROTULO_FORMATO } from "../../types/relatorios";

type Props = {
  /** Disparado quando o usuário escolhe um formato. */
  onExportar: (formato: FormatoExportacao) => void | Promise<void>;
  /** Indica que uma exportação está em andamento (qualquer formato). */
  loading?: boolean;
  /** Restringe os formatos disponíveis (default: csv + pdf + xlsx). */
  formatos?: FormatoExportacao[];
  /** Desabilita o controle. */
  disabled?: boolean;
};

const FORMATOS_PADRAO: FormatoExportacao[] = ["pdf", "xlsx", "csv"];

/**
 * Dropdown reutilizável para exportar relatórios em PDF, Excel (XLSX) ou CSV.
 *
 * O clique no botão principal abre o menu; o item escolhido dispara
 * `onExportar(formato)`. O componente é puro UI — quem chama é responsável
 * por baixar o arquivo correspondente.
 */
export function BotoesExportacao({
  onExportar,
  loading,
  formatos = FORMATOS_PADRAO,
  disabled,
}: Props) {
  const items: MenuProps["items"] = formatos.map((f) => ({
    key: f,
    label: `Exportar ${ROTULO_FORMATO[f]}`,
  }));

  const handleSelect: MenuProps["onClick"] = ({ key }) => {
    void onExportar(key as FormatoExportacao);
  };

  return (
    <Dropdown.Button
      type="primary"
      icon={<DownloadOutlined />}
      menu={{ items, onClick: handleSelect }}
      loading={loading}
      disabled={disabled}
      onClick={() => void onExportar(formatos[0])}
    >
      Exportar {ROTULO_FORMATO[formatos[0]]}
    </Dropdown.Button>
  );
}
