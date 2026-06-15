export type NivelNotificacao = "success" | "error" | "info" | "warning";


export type LinhaNotificacaoUsuario = {
  id: number;
  nivel: NivelNotificacao;
  titulo: string;
  mensagem: string;
  lida_em: string | null;
  criado_em: string;
};


export type NotificacoesPaginadas = {
  total: number;
  proximo: string | null;
  anterior: string | null;
  resultados: LinhaNotificacaoUsuario[];
};


export type VendasPorProdutoPainel = {
  de: string;
  ate: string;
  resumo: {
    faturamento_total: string;
    custo_total: string;
    lucro_total: string;
    margem_percentual: string;
    total_produtos: number;
  };
  top_produtos: Array<{
    sku: string;
    nome: string;
    faturamento_total: string;
    lucro: string;
    margem_percentual: string;
  }>;
};

export type ResumoNotificacoes = {
  gerado_em: string;
  estoque_abaixo_minimo: {
    quantidade: number;
    previa: Array<{
      sku: string;
      nome: string;
      estoque_minimo: string;
      quantidade_atual: string;
      gap: string;
    }>;
  };
  financeiro: {
    hoje: string;
    ate: string;
    dias_a_frente: number;
    vencidos: {
      contagem_pagar: number;
      total_pagar: string;
      contagem_receber: number;
      total_receber: string;
    };
    a_vencer: {
      contagem_pagar: number;
      contagem_receber: number;
    };
  };
  vendas_por_produto?: VendasPorProdutoPainel;
};

