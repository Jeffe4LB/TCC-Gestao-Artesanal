"""Mapeamento de valores de enum API (PT) ↔ modelos Django (EN)."""

from rest_framework import serializers

from estoque.models import MovimentacaoEstoque
from financeiro.models import ContaPagar, ContaReceber, DocumentoFinanceiro
from produtos.models import Produto

SITUACAO_PAGAR_PARA_API = {
    ContaPagar.Situacao.ABERTO: "aberto",
    ContaPagar.Situacao.PARCIAL: "parcial",
    ContaPagar.Situacao.PAGO: "pago",
    ContaPagar.Situacao.CANCELADO: "cancelado",
}
SITUACAO_PAGAR_DO_API = {v: k for k, v in SITUACAO_PAGAR_PARA_API.items()}

SITUACAO_RECEBER_PARA_API = {
    ContaReceber.Situacao.ABERTO: "aberto",
    ContaReceber.Situacao.PARCIAL: "parcial",
    ContaReceber.Situacao.RECEBIDO: "recebido",
    ContaReceber.Situacao.CANCELADO: "cancelado",
}
SITUACAO_RECEBER_DO_API = {v: k for k, v in SITUACAO_RECEBER_PARA_API.items()}

TIPO_DOCUMENTO_PARA_API = {
    DocumentoFinanceiro.Tipo.PAGAR: "pagar",
    DocumentoFinanceiro.Tipo.RECEBER: "receber",
}
TIPO_DOCUMENTO_DO_API = {v: k for k, v in TIPO_DOCUMENTO_PARA_API.items()}

SITUACAO_DOCUMENTO_PARA_API = {
    DocumentoFinanceiro.Situacao.ABERTO: "aberto",
    DocumentoFinanceiro.Situacao.QUITADO: "quitado",
    DocumentoFinanceiro.Situacao.CANCELADO: "cancelado",
}
SITUACAO_DOCUMENTO_DO_API = {v: k for k, v in SITUACAO_DOCUMENTO_PARA_API.items()}

TIPO_PRODUTO_PARA_API = {
    Produto.TipoProduto.COMPRADO: "comprado",
    Produto.TipoProduto.FABRICADO: "fabricado",
}
TIPO_PRODUTO_DO_API = {v: k for k, v in TIPO_PRODUTO_PARA_API.items()}

ORIGEM_CUSTO_PARA_API = {
    "purchase": "aquisicao",
    "bom": "receita",
}
ORIGEM_CUSTO_DO_API = {v: k for k, v in ORIGEM_CUSTO_PARA_API.items()}

TIPO_MOVIMENTACAO_PARA_API = {
    MovimentacaoEstoque.TipoMovimentacao.ENTRADA_COMPRA: "entrada_compra",
    MovimentacaoEstoque.TipoMovimentacao.AJUSTE: "ajuste",
    MovimentacaoEstoque.TipoMovimentacao.CONSUMO_PRODUCAO: "consumo_producao",
    MovimentacaoEstoque.TipoMovimentacao.ENTRADA_PRODUCAO: "entrada_producao",
    MovimentacaoEstoque.TipoMovimentacao.VENDA_RECEBER: "venda_receber",
    MovimentacaoEstoque.TipoMovimentacao.ESTORNO_VENDA_RECEBER: "estorno_venda_receber",
    MovimentacaoEstoque.TipoMovimentacao.ESTORNO_ENTRADA_PRODUCAO: "estorno_entrada_producao",
    MovimentacaoEstoque.TipoMovimentacao.ESTORNO_CONSUMO_PRODUCAO: "estorno_consumo_producao",
}
TIPO_MOVIMENTACAO_DO_API = {v: k for k, v in TIPO_MOVIMENTACAO_PARA_API.items()}
# Chave API legada (nome incorreto); aceita em filtros e payloads antigos.
TIPO_MOVIMENTACAO_ALIASES_DO_API = {
    "saida_producao": MovimentacaoEstoque.TipoMovimentacao.ENTRADA_PRODUCAO,
}


def _map_choice(value, para_api: dict, do_api: dict, label: str):
    if value in para_api:
        return para_api[value]
    if value in do_api:
        return do_api[value]
    raise serializers.ValidationError(f"{label} inválido.")


def situacao_pagar_para_api(value: str) -> str:
    return SITUACAO_PAGAR_PARA_API.get(value, value)


def situacao_pagar_do_api(value: str) -> str:
    return _map_choice(value, SITUACAO_PAGAR_PARA_API, SITUACAO_PAGAR_DO_API, "Situação")


def situacao_receber_para_api(value: str) -> str:
    return SITUACAO_RECEBER_PARA_API.get(value, value)


def situacao_receber_do_api(value: str) -> str:
    return _map_choice(value, SITUACAO_RECEBER_PARA_API, SITUACAO_RECEBER_DO_API, "Situação")


def tipo_produto_para_api(value: str) -> str:
    return TIPO_PRODUTO_PARA_API.get(value, value)


def tipo_produto_do_api(value: str) -> str:
    return _map_choice(value, TIPO_PRODUTO_PARA_API, TIPO_PRODUTO_DO_API, "Tipo de produto")


def origem_custo_para_api(value: str) -> str:
    return ORIGEM_CUSTO_PARA_API.get(value, value)


def origem_custo_do_api(value: str) -> str:
    return _map_choice(value, ORIGEM_CUSTO_PARA_API, ORIGEM_CUSTO_DO_API, "Origem do custo")


def tipo_movimentacao_para_api(value: str) -> str:
    return TIPO_MOVIMENTACAO_PARA_API.get(value, value)


def tipo_movimentacao_do_api(value: str) -> str:
    alias = TIPO_MOVIMENTACAO_ALIASES_DO_API.get(value)
    if alias is not None:
        return alias
    return _map_choice(
        value, TIPO_MOVIMENTACAO_PARA_API, TIPO_MOVIMENTACAO_DO_API, "Tipo de movimentação"
    )


def tipo_documento_para_api(value: str) -> str:
    return TIPO_DOCUMENTO_PARA_API.get(value, value)


def tipo_documento_do_api(value: str) -> str:
    return _map_choice(value, TIPO_DOCUMENTO_PARA_API, TIPO_DOCUMENTO_DO_API, "Tipo do documento")


def situacao_documento_para_api(value: str) -> str:
    return SITUACAO_DOCUMENTO_PARA_API.get(value, value)


def situacao_documento_do_api(value: str) -> str:
    return _map_choice(
        value, SITUACAO_DOCUMENTO_PARA_API, SITUACAO_DOCUMENTO_DO_API, "Situação do documento"
    )
