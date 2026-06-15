from rest_framework import serializers

from .api_enums import (
    origem_custo_do_api,
    origem_custo_para_api,
    situacao_documento_do_api,
    situacao_documento_para_api,
    situacao_pagar_do_api,
    situacao_pagar_para_api,
    situacao_receber_do_api,
    situacao_receber_para_api,
    tipo_documento_do_api,
    tipo_documento_para_api,
    tipo_movimentacao_do_api,
    tipo_movimentacao_para_api,
    tipo_produto_do_api,
    tipo_produto_para_api,
)


class CampoSituacaoPagar(serializers.Field):
    def to_representation(self, value):
        return situacao_pagar_para_api(value)

    def to_internal_value(self, data):
        return situacao_pagar_do_api(str(data))


class CampoSituacaoReceber(serializers.Field):
    def to_representation(self, value):
        return situacao_receber_para_api(value)

    def to_internal_value(self, data):
        return situacao_receber_do_api(str(data))


class CampoTipoProduto(serializers.Field):
    def to_representation(self, value):
        return tipo_produto_para_api(value)

    def to_internal_value(self, data):
        return tipo_produto_do_api(str(data))


class CampoOrigemCusto(serializers.Field):
    def to_representation(self, value):
        return origem_custo_para_api(value)

    def to_internal_value(self, data):
        return origem_custo_do_api(str(data))


class CampoTipoMovimentacao(serializers.Field):
    def to_representation(self, value):
        return tipo_movimentacao_para_api(value)

    def to_internal_value(self, data):
        return tipo_movimentacao_do_api(str(data))


class CampoTipoDocumento(serializers.Field):
    def to_representation(self, value):
        return tipo_documento_para_api(value)

    def to_internal_value(self, data):
        return tipo_documento_do_api(str(data))


class CampoSituacaoDocumento(serializers.Field):
    def to_representation(self, value):
        return situacao_documento_para_api(value)

    def to_internal_value(self, data):
        return situacao_documento_do_api(str(data))
