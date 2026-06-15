import { useMemo } from "react";
import { DatePicker, Form, Input, InputNumber, Select, Slider, Space } from "antd";
import dayjs from "dayjs";
import type { IntervaloParcelamento } from "../../types/financeiro";
import { gerarPreviewParcelas, intervaloParaDias } from "./utilsParcelamento";
import { TabelaParcelas } from "./TabelaParcelas";
import type { ParcelaDocumento } from "../../types/financeiro";

export type ValoresFormularioParcelamento = {
  valorTotal: string;
  numeroParcelas: number;
  primeiraData: string;
  intervalo: IntervaloParcelamento;
  intervaloDiasCustom: number;
};

type Props = {
  valores: ValoresFormularioParcelamento;
  onChange: (patch: Partial<ValoresFormularioParcelamento>) => void;
};

export function FormularioParcelamento({ valores, onChange }: Props) {
  const intervaloDias = intervaloParaDias(valores.intervalo, valores.intervaloDiasCustom);
  const valorNum = Number(String(valores.valorTotal).replace(",", ".")) || 0;

  const preview = useMemo(
    () =>
      gerarPreviewParcelas(
        valorNum,
        valores.numeroParcelas,
        valores.primeiraData,
        intervaloDias,
      ),
    [valorNum, valores.numeroParcelas, valores.primeiraData, intervaloDias],
  );

  const parcelasPreview: ParcelaDocumento[] = preview.map((p) => ({
    id: p.numero,
    numero_parcela: p.numero,
    total_parcelas: valores.numeroParcelas,
    descricao: `Parcela ${p.numero}`,
    valor: p.valor,
    valor_pago: "0.00",
    saldo_restante: p.valor,
    vencimento: p.vencimento,
    situacao: "aberto",
  }));

  return (
    <Space direction="vertical" size="middle" style={{ width: "100%" }}>
      <Form layout="vertical">
        <Form.Item label="Valor total (R$)" required>
          <Input
            value={valores.valorTotal}
            onChange={(e) => onChange({ valorTotal: e.target.value })}
            placeholder="0,00"
          />
        </Form.Item>
        <Form.Item label={`Número de parcelas: ${valores.numeroParcelas}`}>
          <Slider
            min={1}
            max={36}
            value={valores.numeroParcelas}
            onChange={(n) => onChange({ numeroParcelas: n })}
          />
        </Form.Item>
        <Form.Item label="Data da 1ª parcela" required>
          <DatePicker
            style={{ width: "100%" }}
            format="YYYY-MM-DD"
            value={valores.primeiraData ? dayjs(valores.primeiraData) : null}
            onChange={(_, s) => onChange({ primeiraData: typeof s === "string" ? s : "" })}
          />
        </Form.Item>
        <Form.Item label="Intervalo entre parcelas">
          <Select
            value={valores.intervalo}
            onChange={(v: IntervaloParcelamento) => onChange({ intervalo: v })}
            options={[
              { value: "mensal", label: "Mensal (30 dias)" },
              { value: "quinzenal", label: "Quinzenal (15 dias)" },
              { value: "custom", label: "Personalizado (dias)" },
            ]}
          />
        </Form.Item>
        {valores.intervalo === "custom" ? (
          <Form.Item label="Dias entre parcelas">
            <InputNumber
              min={1}
              max={365}
              style={{ width: "100%" }}
              value={valores.intervaloDiasCustom}
              onChange={(n) => onChange({ intervaloDiasCustom: n ?? 30 })}
            />
          </Form.Item>
        ) : null}
      </Form>

      {parcelasPreview.length > 0 ? (
        <>
          <strong>Prévia das parcelas</strong>
          <TabelaParcelas parcelas={parcelasPreview} tipo="pagar" />
        </>
      ) : null}
    </Space>
  );
}
