import { Table } from "antd";
import type { ReactNode } from "react";

export type CelulaTotal = {
  /** Conteúdo da célula; use null para célula vazia. */
  conteudo: ReactNode;
  alinhar?: "left" | "center" | "right";
};

type Props = {
  celulas: CelulaTotal[];
};

/** Linha de totais fixa no rodapé de tabelas de relatório. */
export function RodapeTotaisTabela({ celulas }: Props) {
  return (
    <Table.Summary fixed>
      <Table.Summary.Row>
        {celulas.map((cel, idx) => (
          <Table.Summary.Cell key={idx} index={idx} align={cel.alinhar ?? "left"}>
            {cel.conteudo}
          </Table.Summary.Cell>
        ))}
      </Table.Summary.Row>
    </Table.Summary>
  );
}
