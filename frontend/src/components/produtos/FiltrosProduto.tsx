import { Button, Card, Input, Select, Space } from "antd";
import type { Categoria } from "../../types/cadastro";

export type FiltrosProdutoProps = {
  searchInput: string;
  onSearchInputChange: (value: string) => void;
  filterCategoria: string;
  onFilterCategoriaChange: (value: string) => void;
  filterTipo: string;
  onFilterTipoChange: (value: string) => void;
  filterAtivo: string;
  onFilterAtivoChange: (value: string) => void;
  categories: Categoria[];
  onBuscar: () => void;
};

export function FiltrosProduto({
  searchInput,
  onSearchInputChange,
  filterCategoria,
  onFilterCategoriaChange,
  filterTipo,
  onFilterTipoChange,
  filterAtivo,
  onFilterAtivoChange,
  categories,
  onBuscar,
}: FiltrosProdutoProps) {
  return (
    <Card size="small" title="Filtros">
      <Space wrap>
        <Input
          placeholder="Buscar código, nome ou descrição"
          value={searchInput}
          onChange={(e) => onSearchInputChange(e.target.value)}
          onPressEnter={onBuscar}
          style={{ width: 200 }}
          allowClear
        />
        <Select
          placeholder="Categoria"
          value={filterCategoria || undefined}
          onChange={(v) => onFilterCategoriaChange(v ?? "")}
          allowClear
          style={{ width: 200 }}
          options={categories.map((c) => ({ value: String(c.id), label: c.nome }))}
        />
        <Select
          placeholder="Tipo"
          value={filterTipo || undefined}
          onChange={(v) => onFilterTipoChange(v ?? "")}
          allowClear
          style={{ width: 180 }}
          options={[
            { value: "comprado", label: "Comprado" },
            { value: "fabricado", label: "Produzido" },
          ]}
        />
        <Select
          placeholder="Ativo?"
          value={filterAtivo || undefined}
          onChange={(v) => onFilterAtivoChange(v ?? "")}
          allowClear
          style={{ width: 120 }}
          options={[
            { value: "true", label: "Sim" },
            { value: "false", label: "Não" },
          ]}
        />
        <Button type="primary" onClick={onBuscar}>
          Buscar
        </Button>
      </Space>
    </Card>
  );
}
