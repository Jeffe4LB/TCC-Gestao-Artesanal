from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from clientes.models import Cliente
from estoque.services import sincronizar_estoque_conta_receber
from nucleo.api_enums import situacao_pagar_para_api, situacao_receber_para_api
from nucleo.serializer_fields import (
    CampoSituacaoDocumento,
    CampoSituacaoPagar,
    CampoSituacaoReceber,
    CampoTipoDocumento,
)
from nucleo.units import normalize_unit_code
from produtos.models import Fornecedor

from .models import ContaPagar, ContaReceber, DocumentoFinanceiro, LinhaContaPagar, LinhaContaReceber
from .services import criar_documento_com_parcelas, quantizar_moeda


def _money(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _compute_line_total(quantity, unit_price, discount) -> Decimal:
    return _money(Decimal(str(quantity)) * Decimal(str(unit_price)) - Decimal(str(discount)))


class ContaPagarSerializer(serializers.ModelSerializer):
    nome_fornecedor = serializers.CharField(
        source="fornecedor.nome", read_only=True, allow_null=True
    )
    fornecedor = serializers.PrimaryKeyRelatedField(
        queryset=Fornecedor.objects.all(),
        allow_null=True,
        required=False,
    )
    situacao = CampoSituacaoPagar()
    saldo_restante = serializers.SerializerMethodField()
    rotulo_parcela = serializers.SerializerMethodField()

    class Meta:
        model = ContaPagar
        fields = (
            "id",
            "documento",
            "numero_parcela",
            "total_parcelas",
            "rotulo_parcela",
            "fornecedor",
            "nome_fornecedor",
            "descricao",
            "valor",
            "valor_pago",
            "saldo_restante",
            "vencimento",
            "situacao",
            "pago_em",
            "observacoes",
            "criado_por",
            "criado_em",
            "atualizado_em",
        )
        read_only_fields = (
            "id",
            "documento",
            "numero_parcela",
            "total_parcelas",
            "rotulo_parcela",
            "nome_fornecedor",
            "valor_pago",
            "saldo_restante",
            "criado_por",
            "criado_em",
            "atualizado_em",
        )

    def get_saldo_restante(self, obj: ContaPagar) -> str:
        return str(obj.saldo_restante)

    def get_rotulo_parcela(self, obj: ContaPagar) -> str | None:
        if not obj.documento_id or obj.total_parcelas <= 1:
            return None
        return f"{obj.numero_parcela}/{obj.total_parcelas}"

    def validate_valor(self, value):
        v = _money(value)
        if v <= 0:
            raise serializers.ValidationError("Valor deve ser maior que zero.")
        return v

    def validate(self, attrs):
        situacao = attrs.get("situacao")
        if situacao is None and self.instance:
            situacao = self.instance.situacao
        elif situacao is None:
            situacao = ContaPagar.Situacao.ABERTO
        if "pago_em" in attrs:
            pago_em = attrs.get("pago_em")
        else:
            pago_em = self.instance.pago_em if self.instance else None

        if situacao == ContaPagar.Situacao.PAGO:
            if not pago_em:
                raise serializers.ValidationError(
                    {"pago_em": "Informe a data efetiva do pagamento ao marcar como pago."}
                )
            attrs["valor_pago"] = attrs.get("valor") or (
                self.instance.valor if self.instance else None
            )
        elif situacao == ContaPagar.Situacao.PARCIAL:
            attrs["pago_em"] = None
        else:
            attrs["pago_em"] = None
            if situacao == ContaPagar.Situacao.ABERTO:
                attrs["valor_pago"] = Decimal("0")
        return attrs


class LinhaContaPagarSerializer(serializers.ModelSerializer):
    codigo_produto = serializers.CharField(source="produto.sku", read_only=True)
    nome_produto = serializers.CharField(source="produto.nome", read_only=True)

    class Meta:
        model = LinhaContaPagar
        fields = (
            "id",
            "produto",
            "codigo_produto",
            "nome_produto",
            "quantidade",
            "unidade",
            "custo_unitario",
            "total_linha",
        )
        read_only_fields = ("id", "codigo_produto", "nome_produto", "total_linha")

    def validate_unidade(self, value: str) -> str:
        try:
            return normalize_unit_code(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_custo_unitario(self, value):
        v = quantizar_moeda(value)
        if v <= 0:
            raise serializers.ValidationError("Custo unitário deve ser maior que zero.")
        return v


class LinhaContaReceberSerializer(serializers.ModelSerializer):
    codigo_produto = serializers.SerializerMethodField()

    def get_codigo_produto(self, obj: LinhaContaReceber):
        return obj.produto.sku if obj.produto_id else None

    class Meta:
        model = LinhaContaReceber
        fields = (
            "id",
            "produto",
            "codigo_produto",
            "quantidade",
            "unidade",
            "preco_unitario",
            "desconto",
            "total_linha",
        )
        read_only_fields = ("id", "codigo_produto", "total_linha")

    def validate_unidade(self, value: str) -> str:
        try:
            return normalize_unit_code(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_quantidade(self, value: Decimal) -> Decimal:
        if value <= 0:
            raise serializers.ValidationError("Quantidade deve ser maior que zero.")
        return value

    def validate_preco_unitario(self, value: Decimal) -> Decimal:
        v = _money(value)
        if v <= 0:
            raise serializers.ValidationError("Preço unitário deve ser maior que zero.")
        return v

    def validate_desconto(self, value: Decimal) -> Decimal:
        if value < 0:
            raise serializers.ValidationError("Desconto não pode ser negativo.")
        return _money(value)


def _receivable_stock_user(serializer) -> object | None:
    request = serializer.context.get("request")
    if request and request.user.is_authenticated:
        return request.user
    return None


class ContaReceberSerializer(serializers.ModelSerializer):
    nome_cliente = serializers.CharField(
        source="cliente.nome", read_only=True, allow_null=True
    )
    cliente = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.all(),
        allow_null=True,
        required=False,
    )
    valor = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    situacao = CampoSituacaoReceber()
    saldo_restante = serializers.SerializerMethodField()
    rotulo_parcela = serializers.SerializerMethodField()
    linhas = LinhaContaReceberSerializer(many=True)

    class Meta:
        model = ContaReceber
        fields = (
            "id",
            "documento",
            "numero_parcela",
            "total_parcelas",
            "rotulo_parcela",
            "cliente",
            "nome_cliente",
            "descricao",
            "data_emissao",
            "valor",
            "valor_pago",
            "saldo_restante",
            "vencimento",
            "situacao",
            "recebido_em",
            "observacoes",
            "linhas",
            "criado_por",
            "criado_em",
            "atualizado_em",
        )
        read_only_fields = (
            "id",
            "documento",
            "numero_parcela",
            "total_parcelas",
            "rotulo_parcela",
            "nome_cliente",
            "valor",
            "valor_pago",
            "saldo_restante",
            "criado_por",
            "criado_em",
            "atualizado_em",
        )

    def get_saldo_restante(self, obj: ContaReceber) -> str:
        return str(obj.saldo_restante)

    def get_rotulo_parcela(self, obj: ContaReceber) -> str | None:
        if not obj.documento_id or obj.total_parcelas <= 1:
            return None
        return f"{obj.numero_parcela}/{obj.total_parcelas}"

    def validate_linhas(self, lines):
        if not lines:
            raise serializers.ValidationError("Informe ao menos uma linha com produto e valores.")
        for i, row in enumerate(lines):
            if row.get("produto") is None:
                raise serializers.ValidationError(
                    f"Linha {i + 1}: selecione o produto (lançamentos antigos sem produto devem ser reeditados)."
                )
        return lines

    def validate(self, attrs):
        situacao = attrs.get("situacao")
        if situacao is None and self.instance:
            situacao = self.instance.situacao
        elif situacao is None:
            situacao = ContaReceber.Situacao.ABERTO
        if "recebido_em" in attrs:
            recebido_em = attrs.get("recebido_em")
        else:
            recebido_em = self.instance.recebido_em if self.instance else None

        if situacao == ContaReceber.Situacao.RECEBIDO:
            if not recebido_em:
                raise serializers.ValidationError(
                    {
                        "recebido_em": "Informe a data efetiva do recebimento ao marcar como recebido."
                    }
                )
            attrs["valor_pago"] = attrs.get("valor") or (
                self.instance.valor if self.instance else None
            )
        elif situacao == ContaReceber.Situacao.PARCIAL:
            attrs["recebido_em"] = None
        else:
            attrs["recebido_em"] = None
            if situacao == ContaReceber.Situacao.ABERTO:
                attrs["valor_pago"] = Decimal("0")
        return attrs

    def _sync_receivable_stock_or_raise(self, conta: ContaReceber) -> None:
        try:
            sincronizar_estoque_conta_receber(
                receivable=conta,
                user=_receivable_stock_user(self),
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def _write_lines(self, conta: ContaReceber, lines_data: list) -> Decimal:
        total = Decimal("0")
        conta.linhas.all().delete()
        for row in lines_data:
            lt = _compute_line_total(
                row["quantidade"], row["preco_unitario"], row.get("desconto", 0)
            )
            if lt < 0:
                raise serializers.ValidationError(
                    {"linhas": "Total da linha não pode ser negativo (verifique desconto)."}
                )
            LinhaContaReceber.objects.create(
                conta_receber=conta,
                produto_id=row["produto"].pk if hasattr(row["produto"], "pk") else row["produto"],
                quantidade=row["quantidade"],
                unidade=row["unidade"],
                preco_unitario=row["preco_unitario"],
                desconto=row.get("desconto", 0),
                total_linha=lt,
            )
            total += lt
        return _money(total)

    @transaction.atomic
    def create(self, validated_data):
        lines_data = validated_data.pop("linhas")
        ar = ContaReceber.objects.create(valor=Decimal("0"), **validated_data)
        total = self._write_lines(ar, lines_data)
        ar.valor = total
        ar.save(update_fields=["valor", "atualizado_em"])
        self._sync_receivable_stock_or_raise(ar)
        return ar

    @transaction.atomic
    def update(self, instance, validated_data):
        lines_data = validated_data.pop("linhas", None)
        old_situacao = instance.situacao
        situacao_in_payload = "situacao" in validated_data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if lines_data is not None:
            total = self._write_lines(instance, lines_data)
            instance.valor = total
            instance.save(update_fields=["valor", "atualizado_em"])
        else:
            lst = list(instance.linhas.all())
            if lst:
                total = _money(sum((ln.total_linha for ln in lst), Decimal("0")))
                if instance.valor != total:
                    instance.valor = total
                    instance.save(update_fields=["valor", "atualizado_em"])
        instance.refresh_from_db()
        new_situacao = instance.situacao
        need_stock_sync = lines_data is not None or (
            situacao_in_payload
            and (
                new_situacao == ContaReceber.Situacao.CANCELADO
                or old_situacao == ContaReceber.Situacao.CANCELADO
            )
        )
        if need_stock_sync:
            self._sync_receivable_stock_or_raise(instance)
        return instance


class ParcelaResumoSerializer(serializers.Serializer):
    """Resumo de parcela dentro de um documento financeiro."""

    id = serializers.IntegerField()
    numero_parcela = serializers.IntegerField()
    total_parcelas = serializers.IntegerField()
    descricao = serializers.CharField()
    valor = serializers.DecimalField(max_digits=14, decimal_places=2)
    valor_pago = serializers.DecimalField(max_digits=14, decimal_places=2)
    saldo_restante = serializers.DecimalField(max_digits=14, decimal_places=2)
    vencimento = serializers.DateField()
    situacao = serializers.CharField()


class DocumentoFinanceiroCriacaoSerializer(serializers.Serializer):
    tipo = CampoTipoDocumento()
    fornecedor = serializers.PrimaryKeyRelatedField(
        queryset=Fornecedor.objects.all(), allow_null=True, required=False
    )
    cliente = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.all(), allow_null=True, required=False
    )
    descricao = serializers.CharField(max_length=300)
    valor_total = serializers.DecimalField(max_digits=14, decimal_places=2)
    numero_parcelas = serializers.IntegerField(min_value=1, max_value=36)
    primeira_data = serializers.DateField()
    intervalo_dias = serializers.IntegerField(min_value=0, max_value=365, default=30)
    observacoes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        tipo = attrs["tipo"]
        if tipo == DocumentoFinanceiro.Tipo.PAGAR and not attrs.get("fornecedor"):
            raise serializers.ValidationError(
                {"fornecedor": "Informe o fornecedor para documentos a pagar."}
            )
        if tipo == DocumentoFinanceiro.Tipo.RECEBER and not attrs.get("cliente"):
            raise serializers.ValidationError(
                {"cliente": "Informe o cliente para documentos a receber."}
            )
        if tipo == DocumentoFinanceiro.Tipo.PAGAR and attrs.get("cliente"):
            raise serializers.ValidationError({"cliente": "Não use cliente em documento a pagar."})
        if tipo == DocumentoFinanceiro.Tipo.RECEBER and attrs.get("fornecedor"):
            raise serializers.ValidationError(
                {"fornecedor": "Não use fornecedor em documento a receber."}
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get("request")
        usuario = request.user if request and request.user.is_authenticated else None
        tipo_api = validated_data["tipo"]
        tipo_str = "pagar" if tipo_api == DocumentoFinanceiro.Tipo.PAGAR else "receber"
        return criar_documento_com_parcelas(
            tipo=tipo_str,
            valor_total=validated_data["valor_total"],
            numero_parcelas=validated_data["numero_parcelas"],
            primeira_data=validated_data["primeira_data"],
            intervalo_dias=validated_data.get("intervalo_dias", 30),
            descricao=validated_data["descricao"],
            fornecedor=validated_data.get("fornecedor"),
            cliente=validated_data.get("cliente"),
            observacoes=validated_data.get("observacoes", ""),
            usuario=usuario,
        )


class DocumentoFinanceiroSerializer(serializers.ModelSerializer):
    tipo = CampoTipoDocumento()
    situacao = CampoSituacaoDocumento(read_only=True)
    nome_fornecedor = serializers.CharField(
        source="fornecedor.nome", read_only=True, allow_null=True
    )
    nome_cliente = serializers.CharField(source="cliente.nome", read_only=True, allow_null=True)
    parcelas = serializers.SerializerMethodField()

    class Meta:
        model = DocumentoFinanceiro
        fields = (
            "id",
            "tipo",
            "situacao",
            "fornecedor",
            "nome_fornecedor",
            "cliente",
            "nome_cliente",
            "descricao",
            "valor_total",
            "numero_parcelas",
            "data_emissao",
            "observacoes",
            "parcelas",
            "criado_por",
            "criado_em",
            "atualizado_em",
        )
        read_only_fields = fields

    def _parcela_payload(self, parcela) -> dict:
        return {
            "id": parcela.id,
            "numero_parcela": parcela.numero_parcela,
            "total_parcelas": parcela.total_parcelas,
            "descricao": parcela.descricao,
            "valor": str(parcela.valor),
            "valor_pago": str(parcela.valor_pago),
            "saldo_restante": str(parcela.saldo_restante),
            "vencimento": parcela.vencimento.isoformat(),
            "situacao": (
                situacao_pagar_para_api(parcela.situacao)
                if isinstance(parcela, ContaPagar)
                else situacao_receber_para_api(parcela.situacao)
            ),
        }

    def get_parcelas(self, obj: DocumentoFinanceiro) -> list[dict]:
        if obj.tipo == DocumentoFinanceiro.Tipo.PAGAR:
            qs = obj.contas_pagar.order_by("numero_parcela", "id")
        else:
            qs = obj.contas_receber.order_by("numero_parcela", "id")
        return [self._parcela_payload(p) for p in qs]


class QuitarParcelaSerializer(serializers.Serializer):
    parcela_id = serializers.IntegerField()
    valor = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("0.01"))
    data_pagamento = serializers.DateField()


class AlertaContaPagarSerializer(serializers.ModelSerializer):
    nome_fornecedor = serializers.CharField(
        source="fornecedor.nome", read_only=True, allow_null=True
    )

    class Meta:
        model = ContaPagar
        fields = ("id", "descricao", "valor", "vencimento", "nome_fornecedor")


class AlertaContaReceberSerializer(serializers.ModelSerializer):
    nome_cliente = serializers.CharField(
        source="cliente.nome", read_only=True, allow_null=True
    )

    class Meta:
        model = ContaReceber
        fields = ("id", "descricao", "valor", "vencimento", "nome_cliente")


def _rotulo_parcela(obj) -> str | None:
    if not obj.documento_id or obj.total_parcelas <= 1:
        return None
    return f"{obj.numero_parcela}/{obj.total_parcelas}"


class HistoricoTituloReceberSerializer(serializers.ModelSerializer):
    situacao = serializers.SerializerMethodField()
    rotulo_parcela = serializers.SerializerMethodField()

    class Meta:
        model = ContaReceber
        fields = (
            "id",
            "descricao",
            "data_emissao",
            "vencimento",
            "valor",
            "situacao",
            "rotulo_parcela",
            "recebido_em",
        )

    def get_situacao(self, obj: ContaReceber) -> str:
        return situacao_receber_para_api(obj.situacao)

    def get_rotulo_parcela(self, obj: ContaReceber) -> str | None:
        return _rotulo_parcela(obj)


class HistoricoTituloPagarSerializer(serializers.ModelSerializer):
    situacao = serializers.SerializerMethodField()
    rotulo_parcela = serializers.SerializerMethodField()

    class Meta:
        model = ContaPagar
        fields = (
            "id",
            "descricao",
            "vencimento",
            "valor",
            "situacao",
            "rotulo_parcela",
            "pago_em",
        )

    def get_situacao(self, obj: ContaPagar) -> str:
        return situacao_pagar_para_api(obj.situacao)

    def get_rotulo_parcela(self, obj: ContaPagar) -> str | None:
        return _rotulo_parcela(obj)


# Aliases legados
AccountPayableSerializer = ContaPagarSerializer
AccountReceivableLineSerializer = LinhaContaReceberSerializer
AccountReceivableSerializer = ContaReceberSerializer
PayableAlertSerializer = AlertaContaPagarSerializer
ReceivableAlertSerializer = AlertaContaReceberSerializer
