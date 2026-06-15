from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from nucleo.serializer_fields import CampoTipoProduto
from nucleo.units import normalize_unit_code

from .costs import finalizar_custo_unitario_produto, quant_money
from .models import Categoria, Fornecedor, HistoricoPreco, Produto


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ("id", "nome", "criado_em", "atualizado_em")
        read_only_fields = ("id", "criado_em", "atualizado_em")


class FornecedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fornecedor
        fields = (
            "id",
            "nome",
            "razao_social",
            "documento",
            "telefone",
            "email",
            "observacoes",
            "ativo",
            "criado_em",
            "atualizado_em",
        )
        read_only_fields = ("id", "criado_em", "atualizado_em")


class ProdutoSerializer(serializers.ModelSerializer):
    nome_categoria = serializers.CharField(source="categoria.nome", read_only=True)
    nome_fornecedor = serializers.CharField(
        source="fornecedor.nome", read_only=True, allow_null=True
    )
    tipo_produto = CampoTipoProduto()
    origem_custo = serializers.SerializerMethodField(read_only=True)

    def get_origem_custo(self, obj: Produto) -> str:
        if obj.tipo_produto == Produto.TipoProduto.FABRICADO:
            return "receita"
        return "aquisicao"

    def validate_unidade(self, value: str) -> str:
        if value is None or not str(value).strip():
            raise serializers.ValidationError("Selecione a unidade de cadastro.")
        try:
            return normalize_unit_code(value.strip())
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_preco_venda(self, value):
        return quant_money(value)

    def validate_custo_aquisicao(self, value):
        return quant_money(value)

    def validate(self, attrs):
        inst = self.instance
        pt = attrs.get(
            "tipo_produto",
            inst.tipo_produto if inst else Produto.TipoProduto.COMPRADO,
        )
        if pt == Produto.TipoProduto.FABRICADO:
            attrs["custo_aquisicao"] = Decimal("0")
        else:
            puc = attrs.get("custo_aquisicao")
            if puc is None and inst is not None:
                puc = inst.custo_aquisicao
            if puc is None:
                raise serializers.ValidationError(
                    {"custo_aquisicao": "Informe o custo de aquisição por unidade."}
                )
            if quant_money(puc) <= 0:
                raise serializers.ValidationError(
                    {"custo_aquisicao": "Custo de aquisição deve ser maior que zero."}
                )

        pv = attrs.get("preco_venda")
        if pv is None and inst is not None:
            pv = inst.preco_venda
        else:
            pv = quant_money(pv if pv is not None else Decimal("0"))
            attrs["preco_venda"] = pv
        if pt == Produto.TipoProduto.FABRICADO and pv <= 0:
            raise serializers.ValidationError(
                {
                    "preco_venda": (
                        "Preço de venda deve ser maior que zero para produto fabricado."
                    )
                }
            )
        return attrs

    def create(self, validated_data):
        obj = super().create(validated_data)
        finalizar_custo_unitario_produto(obj)
        return obj

    def update(self, instance, validated_data):
        obj = super().update(instance, validated_data)
        finalizar_custo_unitario_produto(obj)
        return obj

    class Meta:
        model = Produto
        fields = (
            "id",
            "sku",
            "nome",
            "descricao",
            "categoria",
            "nome_categoria",
            "fornecedor",
            "nome_fornecedor",
            "tipo_produto",
            "unidade",
            "preco_venda",
            "custo_aquisicao",
            "custo_unitario",
            "origem_custo",
            "estoque_minimo",
            "ativo",
            "criado_em",
            "atualizado_em",
        )
        read_only_fields = (
            "id",
            "nome_categoria",
            "nome_fornecedor",
            "custo_unitario",
            "origem_custo",
            "criado_em",
            "atualizado_em",
        )


class HistoricoPrecoSerializer(serializers.ModelSerializer):
    alterado_por_nome = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = HistoricoPreco
        fields = (
            "id",
            "preco_venda_anterior",
            "preco_venda_novo",
            "custo_anterior",
            "custo_novo",
            "alterado_por",
            "alterado_por_nome",
            "alterado_em",
        )
        read_only_fields = fields

    def get_alterado_por_nome(self, obj: HistoricoPreco) -> str | None:
        if obj.alterado_por_id is None:
            return None
        return obj.alterado_por.get_username()
