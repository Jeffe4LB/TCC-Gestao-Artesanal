from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from nucleo.serializer_fields import CampoTipoMovimentacao
from nucleo.units import (
    assert_same_unit_category,
    base_unit_for_product_unit,
    convert_quantity,
    normalize_unit_code,
    quantity_to_base,
    signed_quantity_to_base,
)
from produtos.costs import finalizar_custo_unitario_produto
from produtos.models import Produto

from .models import (
    LinhaOrdemProducao,
    LinhaReceita,
    MovimentacaoEstoque,
    OrdemProducao,
    Receita,
    SaldoEstoque,
)
from .services import aplicar_movimentacao, executar_producao, registrar_entrada_compra


def _recipe_line_quantity_to_catalog(*, insumo: Produto, quantity: Decimal, unit_raw: str) -> Decimal:
    s = (unit_raw or "").strip()
    if not s:
        return quantity
    u = normalize_unit_code(s)
    assert_same_unit_category(u, insumo.unidade)
    return convert_quantity(quantity, u, insumo.unidade)


class SaldoEstoqueSerializer(serializers.ModelSerializer):
    codigo_produto = serializers.CharField(source="produto.sku", read_only=True)
    nome_produto = serializers.CharField(source="produto.nome", read_only=True)
    unidade_base = serializers.SerializerMethodField(read_only=True)

    def get_unidade_base(self, obj: SaldoEstoque) -> str:
        return base_unit_for_product_unit(obj.produto.unidade)

    quantidade_reservada = serializers.DecimalField(
        max_digits=14, decimal_places=3, read_only=True
    )
    disponivel = serializers.SerializerMethodField(read_only=True)

    def get_disponivel(self, obj: SaldoEstoque) -> str:
        return str(obj.disponivel.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP))

    class Meta:
        model = SaldoEstoque
        fields = (
            "id",
            "produto",
            "codigo_produto",
            "nome_produto",
            "quantidade",
            "quantidade_reservada",
            "disponivel",
            "unidade_base",
        )


class AlertaEstoqueBaixoSerializer(serializers.ModelSerializer):
    id_produto = serializers.IntegerField(source="produto.id", read_only=True)
    codigo = serializers.CharField(source="produto.sku", read_only=True)
    nome = serializers.CharField(source="produto.nome", read_only=True)
    estoque_minimo = serializers.DecimalField(
        source="produto.estoque_minimo",
        max_digits=14,
        decimal_places=3,
        read_only=True,
    )
    quantidade_atual = serializers.DecimalField(
        source="quantidade",
        max_digits=14,
        decimal_places=3,
        read_only=True,
    )
    deficit = serializers.SerializerMethodField(read_only=True)
    unidade_base = serializers.SerializerMethodField(read_only=True)

    def get_unidade_base(self, obj: SaldoEstoque) -> str:
        return base_unit_for_product_unit(obj.produto.unidade)

    def get_deficit(self, obj: SaldoEstoque) -> str:
        gap = getattr(obj, "gap", None)
        if gap is not None:
            g = gap
        else:
            min_base = quantity_to_base(obj.produto.estoque_minimo, obj.produto.unidade)
            g = min_base - obj.quantidade
        return str(g.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP))

    class Meta:
        model = SaldoEstoque
        fields = (
            "id_produto",
            "codigo",
            "nome",
            "estoque_minimo",
            "quantidade_atual",
            "deficit",
            "unidade_base",
        )


class MovimentacaoEstoqueSerializer(serializers.ModelSerializer):
    codigo_produto = serializers.CharField(source="produto.sku", read_only=True)
    unidade_base = serializers.SerializerMethodField(read_only=True)
    tipo_movimentacao = CampoTipoMovimentacao(read_only=True)
    criado_por_nome = serializers.SerializerMethodField(read_only=True)

    def get_unidade_base(self, obj: MovimentacaoEstoque) -> str:
        return base_unit_for_product_unit(obj.produto.unidade)

    def get_criado_por_nome(self, obj: MovimentacaoEstoque) -> str | None:
        if obj.criado_por_id is None:
            return None
        return obj.criado_por.username

    class Meta:
        model = MovimentacaoEstoque
        fields = (
            "id",
            "produto",
            "codigo_produto",
            "delta_quantidade",
            "quantidade_informada",
            "unidade_informada",
            "unidade_base",
            "tipo_movimentacao",
            "ordem_producao",
            "conta_pagar",
            "observacoes",
            "criado_por",
            "criado_por_nome",
            "criado_em",
        )


class MovimentacaoEstoqueWriteSerializer(serializers.Serializer):
    tipo_movimentacao = CampoTipoMovimentacao()
    produto = serializers.PrimaryKeyRelatedField(queryset=Produto.objects.filter(ativo=True))
    quantidade = serializers.DecimalField(max_digits=14, decimal_places=3)
    unidade = serializers.CharField(required=False, allow_blank=True, default="")
    observacoes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        mt = attrs["tipo_movimentacao"]
        q: Decimal = attrs["quantidade"]
        product: Produto = attrs["produto"]
        unit_raw = (attrs.get("unidade") or "").strip()
        if unit_raw:
            unit_in = normalize_unit_code(unit_raw)
        else:
            unit_in = base_unit_for_product_unit(product.unidade)
        try:
            assert_same_unit_category(unit_in, product.unidade)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"unidade": list(exc.messages)}) from exc

        if mt == MovimentacaoEstoque.TipoMovimentacao.ENTRADA_COMPRA and q <= 0:
            raise serializers.ValidationError(
                {"quantidade": "Na compra, a quantidade deve ser maior que zero."}
            )
        if mt == MovimentacaoEstoque.TipoMovimentacao.AJUSTE and q == 0:
            raise serializers.ValidationError({"quantidade": "Ajuste não pode ser zero."})

        if mt == MovimentacaoEstoque.TipoMovimentacao.ENTRADA_COMPRA:
            delta = quantity_to_base(q, unit_in)
            q_in = q
        else:
            delta = signed_quantity_to_base(q, unit_in)
            q_in = q

        attrs["delta_quantidade"] = delta
        attrs["unidade_informada"] = unit_in
        attrs["quantidade_informada"] = q_in
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        mt = validated_data.pop("tipo_movimentacao")
        product = validated_data.pop("produto")
        delta: Decimal = validated_data.pop("delta_quantidade")
        notes = validated_data.pop("observacoes", "") or ""
        q_in = validated_data.pop("quantidade_informada", None)
        u_in = validated_data.pop("unidade_informada", None)

        try:
            return aplicar_movimentacao(
                product=product,
                quantity_delta=delta,
                movement_type=mt,
                user=request.user if request.user.is_authenticated else None,
                notes=notes,
                quantity_input=q_in,
                unit_input=u_in,
            )
        except DjangoValidationError as e:
            if hasattr(e, "error_dict") and e.error_dict:
                raise serializers.ValidationError(e.error_dict)
            msgs = getattr(e, "messages", None) or [str(e)]
            raise serializers.ValidationError(msgs)


class LinhaReceitaSerializer(serializers.ModelSerializer):
    codigo_insumo = serializers.CharField(source="insumo.sku", read_only=True)

    class Meta:
        model = LinhaReceita
        fields = ("id", "insumo", "codigo_insumo", "quantidade_por_unidade")
        read_only_fields = ("id", "codigo_insumo")

    def validate_quantidade_por_unidade(self, value: Decimal):
        if value <= 0:
            raise serializers.ValidationError("Deve ser maior que zero.")
        return value


class ReceitaSerializer(serializers.ModelSerializer):
    linhas = LinhaReceitaSerializer(many=True)

    class Meta:
        model = Receita
        fields = ("id", "produto", "observacoes", "linhas", "criado_em", "atualizado_em")
        read_only_fields = ("id", "criado_em", "atualizado_em")

    def validate_produto(self, value: Produto):
        if value.tipo_produto != Produto.TipoProduto.FABRICADO:
            raise serializers.ValidationError(
                "A receita só pode ser associada a produto fabricado manualmente."
            )
        return value

    def validate_linhas(self, lines):
        if not lines:
            raise serializers.ValidationError("Informe ao menos um insumo na receita.")
        return lines

    def create(self, validated_data):
        lines_data = validated_data.pop("linhas")
        raw_lines = self.initial_data.get("linhas") if isinstance(self.initial_data, dict) else None
        receita = Receita.objects.create(**validated_data)
        for i, line in enumerate(lines_data):
            insumo = line["insumo"]
            if insumo.pk == receita.produto_id:
                raise serializers.ValidationError(
                    {"linhas": "Insumo não pode ser o próprio produto fabricado."}
                )
            raw = raw_lines[i] if isinstance(raw_lines, list) and i < len(raw_lines) else {}
            unit_raw = (raw.get("quantidade_por_unidade_unidade") or "").strip() if isinstance(raw, dict) else ""
            try:
                q_cat = _recipe_line_quantity_to_catalog(
                    insumo=insumo, quantity=line["quantidade_por_unidade"], unit_raw=unit_raw
                )
            except DjangoValidationError as exc:
                raise serializers.ValidationError({"linhas": list(exc.messages)}) from exc
            LinhaReceita.objects.create(
                receita=receita,
                insumo=insumo,
                quantidade_por_unidade=q_cat,
            )
        finalizar_custo_unitario_produto(Produto.objects.get(pk=receita.produto_id))
        return receita

    def update(self, instance, validated_data):
        lines_data = validated_data.pop("linhas", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if lines_data is not None:
            if not lines_data:
                raise serializers.ValidationError({"linhas": "Informe ao menos um insumo."})
            raw_lines = self.initial_data.get("linhas") if isinstance(self.initial_data, dict) else None
            instance.linhas.all().delete()
            for i, line in enumerate(lines_data):
                insumo = line["insumo"]
                if insumo.pk == instance.produto_id:
                    raise serializers.ValidationError(
                        {"linhas": "Insumo não pode ser o próprio produto fabricado."}
                    )
                raw = raw_lines[i] if isinstance(raw_lines, list) and i < len(raw_lines) else {}
                unit_raw = (raw.get("quantidade_por_unidade_unidade") or "").strip() if isinstance(raw, dict) else ""
                try:
                    q_cat = _recipe_line_quantity_to_catalog(
                        insumo=insumo, quantity=line["quantidade_por_unidade"], unit_raw=unit_raw
                    )
                except DjangoValidationError as exc:
                    raise serializers.ValidationError({"linhas": list(exc.messages)}) from exc
                LinhaReceita.objects.create(
                    receita=instance,
                    insumo=insumo,
                    quantidade_por_unidade=q_cat,
                )
        finalizar_custo_unitario_produto(instance.produto)
        return instance


class LinhaOrdemProducaoLeituraSerializer(serializers.ModelSerializer):
    codigo_insumo = serializers.CharField(source="insumo.sku", read_only=True)
    nome_insumo = serializers.CharField(source="insumo.nome", read_only=True)

    class Meta:
        model = LinhaOrdemProducao
        fields = ("id", "insumo", "codigo_insumo", "nome_insumo", "quantidade_consumida")


class OrdemProducaoLeituraSerializer(serializers.ModelSerializer):
    codigo_produto = serializers.CharField(source="produto.sku", read_only=True)
    nome_produto = serializers.CharField(source="produto.nome", read_only=True)
    linhas = LinhaOrdemProducaoLeituraSerializer(many=True, read_only=True)
    ativa = serializers.SerializerMethodField()

    class Meta:
        model = OrdemProducao
        fields = (
            "id",
            "produto",
            "codigo_produto",
            "nome_produto",
            "quantidade_produzida",
            "observacoes",
            "linhas",
            "criado_por",
            "criado_em",
            "cancelada_em",
            "cancelada_por",
            "ativa",
        )

    def get_ativa(self, obj) -> bool:
        return obj.cancelada_em is None


class LinhaProducaoInputSerializer(serializers.Serializer):
    insumo = serializers.PrimaryKeyRelatedField(queryset=Produto.objects.filter(ativo=True))
    quantidade_consumida = serializers.DecimalField(max_digits=14, decimal_places=3)
    quantidade_consumida_unidade = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_quantidade_consumida(self, value: Decimal):
        if value <= 0:
            raise serializers.ValidationError("Deve ser maior que zero.")
        return value

    def validate(self, attrs):
        insumo: Produto = attrs["insumo"]
        raw = (attrs.get("quantidade_consumida_unidade") or "").strip()
        if raw:
            try:
                u = normalize_unit_code(raw)
            except DjangoValidationError as exc:
                raise serializers.ValidationError(
                    {"quantidade_consumida_unidade": list(exc.messages)}
                ) from exc
            try:
                assert_same_unit_category(u, insumo.unidade)
            except DjangoValidationError as exc:
                raise serializers.ValidationError(
                    {"quantidade_consumida_unidade": list(exc.messages)}
                ) from exc
        return attrs


class OrdemProducaoCreateSerializer(serializers.Serializer):
    produto = serializers.PrimaryKeyRelatedField(
        queryset=Produto.objects.filter(
            ativo=True,
            tipo_produto=Produto.TipoProduto.FABRICADO,
        ),
    )
    quantidade_produzida = serializers.DecimalField(max_digits=14, decimal_places=3)
    quantidade_produzida_unidade = serializers.CharField(required=False, allow_blank=True, default="")
    linhas = LinhaProducaoInputSerializer(many=True)
    observacoes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_quantidade_produzida(self, value: Decimal):
        if value <= 0:
            raise serializers.ValidationError("Deve ser maior que zero.")
        return value

    def validate(self, attrs):
        product: Produto = attrs["produto"]
        raw = (attrs.get("quantidade_produzida_unidade") or "").strip()
        if raw:
            try:
                u = normalize_unit_code(raw)
            except DjangoValidationError as exc:
                raise serializers.ValidationError(
                    {"quantidade_produzida_unidade": list(exc.messages)}
                ) from exc
            try:
                assert_same_unit_category(u, product.unidade)
            except DjangoValidationError as exc:
                raise serializers.ValidationError(
                    {"quantidade_produzida_unidade": list(exc.messages)}
                ) from exc
        return attrs

    def validate_linhas(self, value):
        if not value:
            raise serializers.ValidationError("Informe ao menos um insumo consumido.")
        seen: set[int] = set()
        for row in value:
            pk = row["insumo"].pk
            if pk in seen:
                raise serializers.ValidationError(
                    "Há insumo repetido nas linhas. Una as quantidades em uma única linha."
                )
            seen.add(pk)
        return value

    def create(self, validated_data):
        request = self.context["request"]
        lines_payload = [
            {
                "component": row["insumo"].pk,
                "quantity_consumed": row["quantidade_consumida"],
                "quantity_consumed_unit": (row.get("quantidade_consumida_unidade") or "").strip() or None,
            }
            for row in validated_data["linhas"]
        ]
        try:
            return executar_producao(
                produto_id=validated_data["produto"].pk,
                quantity_produced=validated_data["quantidade_produzida"],
                quantity_produced_unit=(validated_data.get("quantidade_produzida_unidade") or "").strip()
                or None,
                lines=lines_payload,
                user=request.user if request.user.is_authenticated else None,
                notes=validated_data.get("observacoes") or "",
            )
        except DjangoValidationError as e:
            if hasattr(e, "error_dict") and e.error_dict:
                raise serializers.ValidationError(e.error_dict)
            msgs = getattr(e, "messages", None) or [str(e)]
            raise serializers.ValidationError(msgs)


class LinhaEntradaCompraInputSerializer(serializers.Serializer):
    produto = serializers.PrimaryKeyRelatedField(queryset=Produto.objects.filter(ativo=True))
    quantidade = serializers.DecimalField(max_digits=14, decimal_places=3)
    unidade = serializers.CharField(required=False, allow_blank=True, default="")
    custo_unitario = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        required=False,
        allow_null=True,
    )


class EntradaCompraWriteSerializer(serializers.Serializer):
    fornecedor = serializers.PrimaryKeyRelatedField(
        queryset=Produto.objects.none(),
        required=False,
        allow_null=True,
    )
    descricao = serializers.CharField(max_length=300)
    vencimento = serializers.DateField()
    observacoes = serializers.CharField(required=False, allow_blank=True, default="")
    linhas = LinhaEntradaCompraInputSerializer(many=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from produtos.models import Fornecedor

        self.fields["fornecedor"].queryset = Fornecedor.objects.filter(ativo=True)

    def validate_linhas(self, lines):
        if not lines:
            raise serializers.ValidationError("Informe ao menos uma linha com produto.")
        return lines

    def create(self, validated_data):
        from financeiro.serializers import ContaPagarSerializer, LinhaContaPagarSerializer

        request = self.context["request"]
        lines = validated_data.pop("linhas")
        payload_lines = []
        for row in lines:
            item = {
                "produto": row["produto"].pk,
                "quantidade": row["quantidade"],
                "unidade": (row.get("unidade") or "").strip(),
            }
            if row.get("custo_unitario") is not None:
                item["custo_unitario"] = row["custo_unitario"]
            payload_lines.append(item)

        try:
            result = registrar_entrada_compra(
                fornecedor=validated_data.get("fornecedor"),
                descricao=validated_data["descricao"],
                vencimento=validated_data["vencimento"],
                observacoes=validated_data.get("observacoes") or "",
                linhas=payload_lines,
                user=request.user if request.user.is_authenticated else None,
            )
        except DjangoValidationError as exc:
            if hasattr(exc, "error_dict") and exc.error_dict:
                raise serializers.ValidationError(exc.error_dict) from exc
            msgs = getattr(exc, "messages", None) or [str(exc)]
            raise serializers.ValidationError(msgs) from exc

        payable = result["conta_pagar"]
        ctx = self.context
        return {
            "conta_pagar": ContaPagarSerializer(payable, context=ctx).data,
            "linhas": LinhaContaPagarSerializer(result["linhas"], many=True, context=ctx).data,
            "movimentacoes": MovimentacaoEstoqueSerializer(
                result["movimentacoes"], many=True, context=ctx
            ).data,
        }


# Aliases legados (API/views antigas)
StockBalanceSerializer = SaldoEstoqueSerializer
LowStockAlertSerializer = AlertaEstoqueBaixoSerializer
StockMovementSerializer = MovimentacaoEstoqueSerializer
StockMovementWriteSerializer = MovimentacaoEstoqueWriteSerializer
RecipeLineSerializer = LinhaReceitaSerializer
RecipeSerializer = ReceitaSerializer
ProductionRunLineReadSerializer = LinhaOrdemProducaoLeituraSerializer
ProductionRunReadSerializer = OrdemProducaoLeituraSerializer
ProductionLineInputSerializer = LinhaProducaoInputSerializer
ProductionRunCreateSerializer = OrdemProducaoCreateSerializer
