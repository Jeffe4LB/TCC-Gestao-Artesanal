from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Literal, TypeAlias

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F, Sum
from django.db.models.functions import Coalesce

from nucleo.units import assert_same_unit_category, convert_quantity, normalize_unit_code
from produtos.models import Produto

from .models import ContaPagar, ContaReceber, DocumentoFinanceiro

TipoDocumento = Literal["pagar", "receber"]
Parcela: TypeAlias = ContaPagar | ContaReceber

SITUACOES_EM_ABERTO_PAGAR = (
    ContaPagar.Situacao.ABERTO,
    ContaPagar.Situacao.PARCIAL,
)
SITUACOES_EM_ABERTO_RECEBER = (
    ContaReceber.Situacao.ABERTO,
    ContaReceber.Situacao.PARCIAL,
)


def quantizar_moeda(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


def saldo_restante_expr():
    """Expressão ORM: valor - valor_pago (saldo em aberto da parcela)."""
    return F("valor") - F("valor_pago")


def queryset_contas_em_aberto_pagar():
    return ContaPagar.objects.filter(situacao__in=SITUACOES_EM_ABERTO_PAGAR)


def queryset_contas_em_aberto_receber():
    return ContaReceber.objects.filter(situacao__in=SITUACOES_EM_ABERTO_RECEBER)


def agregar_saldo_restante(qs) -> Decimal:
    total = qs.aggregate(
        t=Coalesce(Sum(saldo_restante_expr()), Decimal("0"))
    )["t"]
    return quantizar_moeda(total)


def calcular_total_linha_compra(
    *,
    quantidade,
    unidade: str,
    produto: Produto,
    custo_unitario,
) -> Decimal:
    """Total em R$; custo unitário é por unidade de cadastro do produto."""
    unit_in = normalize_unit_code(unidade)
    assert_same_unit_category(unit_in, produto.unidade)
    qty_cat = convert_quantity(Decimal(str(quantidade)), unit_in, produto.unidade)
    if qty_cat <= 0:
        raise ValidationError("Quantidade deve ser maior que zero.")
    custo = quantizar_moeda(custo_unitario)
    if custo <= 0:
        raise ValidationError("Custo unitário deve ser maior que zero.")
    return quantizar_moeda(qty_cat * custo)


def _tipo_documento_para_model(tipo: TipoDocumento) -> str:
    if tipo == "pagar":
        return DocumentoFinanceiro.Tipo.PAGAR
    if tipo == "receber":
        return DocumentoFinanceiro.Tipo.RECEBER
    raise ValidationError(f"Tipo de documento inválido: {tipo}")


def _parcelas_do_documento(documento: DocumentoFinanceiro):
    if documento.tipo == DocumentoFinanceiro.Tipo.PAGAR:
        return documento.contas_pagar.order_by("numero_parcela", "id")
    return documento.contas_receber.order_by("numero_parcela", "id")


def _valores_parcelas(valor_total: Decimal, numero_parcelas: int) -> list[Decimal]:
    if numero_parcelas < 1:
        raise ValidationError("Número de parcelas mínimo é 1.")
    valor_total = quantizar_moeda(valor_total)
    if valor_total <= 0:
        raise ValidationError("Valor total deve ser maior que zero.")

    valor_parcela = quantizar_moeda(valor_total / numero_parcelas)
    valores: list[Decimal] = []
    soma = Decimal("0")
    for i in range(numero_parcelas):
        if i < numero_parcelas - 1:
            valores.append(valor_parcela)
            soma += valor_parcela
        else:
            valores.append(quantizar_moeda(valor_total - soma))
    return valores


@transaction.atomic
def criar_documento_com_parcelas(
    *,
    tipo: TipoDocumento,
    valor_total: Decimal,
    numero_parcelas: int,
    primeira_data: date,
    intervalo_dias: int = 30,
    descricao: str = "",
    fornecedor=None,
    cliente=None,
    observacoes: str = "",
    usuario=None,
) -> DocumentoFinanceiro:
    """Cria documento mãe e N parcelas com divisão exata do valor total."""
    if tipo == "pagar" and cliente is not None:
        raise ValidationError("Documento a pagar não deve ter cliente.")
    if tipo == "receber" and fornecedor is not None:
        raise ValidationError("Documento a receber não deve ter fornecedor.")
    if intervalo_dias < 0:
        raise ValidationError("Intervalo entre parcelas não pode ser negativo.")

    valores = _valores_parcelas(valor_total, numero_parcelas)
    tipo_db = _tipo_documento_para_model(tipo)

    documento = DocumentoFinanceiro.objects.create(
        tipo=tipo_db,
        fornecedor=fornecedor,
        cliente=cliente,
        descricao=descricao.strip() or f"Documento {tipo}",
        valor_total=quantizar_moeda(valor_total),
        numero_parcelas=numero_parcelas,
        data_emissao=primeira_data,
        observacoes=observacoes,
        criado_por=usuario,
    )

    for i, valor in enumerate(valores):
        vencimento = primeira_data + timedelta(days=intervalo_dias * i)
        rotulo = f"{descricao.strip()} ({i + 1}/{numero_parcelas})" if descricao else f"Parcela {i + 1}/{numero_parcelas}"
        if tipo == "pagar":
            ContaPagar.objects.create(
                documento=documento,
                fornecedor=fornecedor,
                descricao=rotulo,
                valor=valor,
                valor_pago=Decimal("0"),
                numero_parcela=i + 1,
                total_parcelas=numero_parcelas,
                vencimento=vencimento,
                criado_por=usuario,
            )
        else:
            ContaReceber.objects.create(
                documento=documento,
                cliente=cliente,
                descricao=rotulo,
                data_emissao=primeira_data,
                valor=valor,
                valor_pago=Decimal("0"),
                numero_parcela=i + 1,
                total_parcelas=numero_parcelas,
                vencimento=vencimento,
                criado_por=usuario,
            )

    return documento


def recalcular_status_documento(documento: DocumentoFinanceiro) -> None:
    """Atualiza situação do documento conforme parcelas filhas."""
    if documento.situacao == DocumentoFinanceiro.Situacao.CANCELADO:
        return

    parcelas = list(_parcelas_do_documento(documento))
    if not parcelas:
        return

    if documento.tipo == DocumentoFinanceiro.Tipo.PAGAR:
        quitado = ContaPagar.Situacao.PAGO
        cancelado = ContaPagar.Situacao.CANCELADO
    else:
        quitado = ContaReceber.Situacao.RECEBIDO
        cancelado = ContaReceber.Situacao.CANCELADO

    ativas = [p for p in parcelas if p.situacao != cancelado]
    if not ativas:
        documento.situacao = DocumentoFinanceiro.Situacao.CANCELADO
    elif all(p.situacao == quitado for p in ativas):
        documento.situacao = DocumentoFinanceiro.Situacao.QUITADO
    else:
        documento.situacao = DocumentoFinanceiro.Situacao.ABERTO

    documento.save(update_fields=["situacao", "atualizado_em"])


@transaction.atomic
def quitar_parcela(
    *,
    parcela: Parcela,
    valor_pago: Decimal,
    data_pagamento: date,
    usuario=None,
) -> Parcela:
    """Registra baixa (total ou parcial) em uma parcela."""
    valor_pago = quantizar_moeda(valor_pago)
    if valor_pago <= 0:
        raise ValidationError("Valor da baixa deve ser maior que zero.")

    if isinstance(parcela, ContaPagar):
        model_cls = ContaPagar
        situacao_quitado = ContaPagar.Situacao.PAGO
        situacao_parcial = ContaPagar.Situacao.PARCIAL
        campo_data = "pago_em"
    else:
        model_cls = ContaReceber
        situacao_quitado = ContaReceber.Situacao.RECEBIDO
        situacao_parcial = ContaReceber.Situacao.PARCIAL
        campo_data = "recebido_em"

    parcela = model_cls.objects.select_for_update().get(pk=parcela.pk)

    if parcela.situacao in (model_cls.Situacao.CANCELADO, situacao_quitado):
        raise ValidationError("Parcela cancelada ou já quitada.")

    novo_valor_pago = quantizar_moeda(parcela.valor_pago + valor_pago)
    if novo_valor_pago > parcela.valor:
        raise ValidationError("Valor pago excede o valor da parcela.")

    parcela.valor_pago = novo_valor_pago
    if novo_valor_pago >= parcela.valor:
        parcela.situacao = situacao_quitado
        setattr(parcela, campo_data, data_pagamento)
    else:
        parcela.situacao = situacao_parcial
        setattr(parcela, campo_data, None)

    update_fields = ["valor_pago", "situacao", campo_data, "atualizado_em"]
    parcela.save(update_fields=update_fields)

    if parcela.documento_id:
        recalcular_status_documento(parcela.documento)

    return parcela


@transaction.atomic
def cancelar_documento(documento: DocumentoFinanceiro) -> DocumentoFinanceiro:
    """Cancela parcelas em aberto/parciais; mantém quitadas."""
    documento = DocumentoFinanceiro.objects.select_for_update().get(pk=documento.pk)
    if documento.situacao == DocumentoFinanceiro.Situacao.CANCELADO:
        return documento

    if documento.tipo == DocumentoFinanceiro.Tipo.PAGAR:
        parcelas = documento.contas_pagar.select_for_update()
        situacao_quitado = ContaPagar.Situacao.PAGO
        situacao_cancelado = ContaPagar.Situacao.CANCELADO
    else:
        parcelas = documento.contas_receber.select_for_update()
        situacao_quitado = ContaReceber.Situacao.RECEBIDO
        situacao_cancelado = ContaReceber.Situacao.CANCELADO

    for parcela in parcelas:
        if parcela.situacao == situacao_quitado:
            continue
        parcela.situacao = situacao_cancelado
        parcela.save(update_fields=["situacao", "atualizado_em"])

    documento.situacao = DocumentoFinanceiro.Situacao.CANCELADO
    documento.save(update_fields=["situacao", "atualizado_em"])
    return documento
