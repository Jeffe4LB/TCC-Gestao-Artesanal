import { Button, Card, DatePicker, Input, Select, Space } from "antd";
import dayjs from "dayjs";
import type { Cliente } from "../../../types/cadastro";

export type FiltrosContaReceberProps = {
  searchInput: string;
  onSearchInputChange: (value: string) => void;
  filterSituacao: string;
  onFilterSituacaoChange: (value: string) => void;
  filterParcelado: string;
  onFilterParceladoChange: (value: string) => void;
  filterCliente: string;
  onFilterClienteChange: (value: string) => void;
  dueFrom: string;
  onDueFromChange: (value: string) => void;
  dueTo: string;
  onDueToChange: (value: string) => void;
  customers: Cliente[];
  onBuscar: () => void;
};

export function FiltrosContaReceber({
  searchInput,
  onSearchInputChange,
  filterSituacao,
  onFilterSituacaoChange,
  filterParcelado,
  onFilterParceladoChange,
  filterCliente,
  onFilterClienteChange,
  dueFrom,
  onDueFromChange,
  dueTo,
  onDueToChange,
  customers,
  onBuscar,
}: FiltrosContaReceberProps) {
  return (
    <Card size="small" title="Filtros">
      <Space wrap>
        <Input
          placeholder="Buscar descrição ou observações"
          value={searchInput}
          onChange={(e) => onSearchInputChange(e.target.value)}
          onPressEnter={onBuscar}
          style={{ width: 220 }}
          allowClear
        />
        <Select
          placeholder="Status"
          value={filterSituacao || undefined}
          onChange={(v) => onFilterSituacaoChange(v ?? "")}
          allowClear
          style={{ width: 160 }}
          options={[
            { value: "aberto", label: "Em aberto" },
            { value: "parcial", label: "Parcial" },
            { value: "recebido", label: "Recebido" },
            { value: "cancelado", label: "Cancelado" },
          ]}
        />
        <Select
          placeholder="Parcelado"
          value={filterParcelado || undefined}
          onChange={(v) => onFilterParceladoChange(v ?? "")}
          allowClear
          style={{ width: 150 }}
          options={[
            { value: "sim", label: "Só parcelado" },
            { value: "nao", label: "Avulso" },
          ]}
        />
        <Select
          placeholder="Cliente"
          value={filterCliente || undefined}
          onChange={(v) => onFilterClienteChange(v ?? "")}
          allowClear
          showSearch
          optionFilterProp="label"
          style={{ width: 220 }}
          options={customers.map((c) => ({ value: String(c.id), label: c.nome }))}
        />
        <DatePicker
          placeholder="Venc. de"
          format="YYYY-MM-DD"
          value={dueFrom ? dayjs(dueFrom) : null}
          onChange={(_, s) => onDueFromChange(typeof s === "string" ? s : "")}
        />
        <DatePicker
          placeholder="Venc. até"
          format="YYYY-MM-DD"
          value={dueTo ? dayjs(dueTo) : null}
          onChange={(_, s) => onDueToChange(typeof s === "string" ? s : "")}
        />
        <Button type="primary" onClick={onBuscar}>
          Buscar
        </Button>
      </Space>
    </Card>
  );
}
