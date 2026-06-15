import { DEFAULT_PRODUCT_UNIT } from "../../../constants/unidades";
import type { ProductUnitCode } from "../../../constants/unidades";
import type { SituacaoReceber } from "../../../types/financeiro";
import { todayLocal } from "../../../utils/data";

export type LinhaFormContaReceber = {
  produto: string;
  quantidade: string;
  unidade: ProductUnitCode;
  preco_unitario: string;
  desconto: string;
};

export type FormContaReceber = {
  cliente: string;
  descricao: string;
  data_emissao: string;
  vencimento: string;
  situacao: SituacaoReceber;
  recebido_em: string;
  observacoes: string;
  linhas: LinhaFormContaReceber[];
};

export const linhaVazia = (): LinhaFormContaReceber => ({
  produto: "",
  quantidade: "1",
  unidade: DEFAULT_PRODUCT_UNIT,
  preco_unitario: "",
  desconto: "0",
});

export const formContaReceberVazio = (): FormContaReceber => ({
  cliente: "",
  descricao: "",
  data_emissao: todayLocal(),
  vencimento: "",
  situacao: "aberto",
  recebido_em: "",
  observacoes: "",
  linhas: [linhaVazia()],
});
