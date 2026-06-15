from decimal import Decimal, InvalidOperation

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Case, IntegerField, Value, When
from django.utils import timezone

from financeiro.models import ContaPagar, ContaReceber, LinhaContaPagar, LinhaContaReceber
from financeiro.services import calcular_total_linha_compra, quantizar_moeda
from nucleo.units import (
    assert_same_unit_category,
    base_unit_for_product_unit,
    normalize_unit_code,
    quantity_to_base,
)
from produtos.models import Fornecedor, Produto

from .models import (
    LinhaOrdemProducao,
    MovimentacaoEstoque,
    OrdemProducao,
    SaldoEstoque,
)

User = get_user_model()


def _to_decimal(value) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValidationError("Quantidade inválida.") from exc


@transaction.atomic
def aplicar_movimentacao(
    *,
    product: Produto,
    quantity_delta: Decimal,
    movement_type: str,
    user: User | None = None,
    ordem_producao=None,
    conta_receber: ContaReceber | None = None,
    conta_pagar: ContaPagar | None = None,
    venda_receber_substituta: bool = False,
    notes: str = "",
    quantity_input: Decimal | None = None,
    unit_input: str | None = None,
) -> MovimentacaoEstoque:
    """
    Atualiza saldo (com lock) e grava movimento.
    ``quantity_delta`` deve estar na **unidade base** (KG, L ou UN).
    """
    if quantity_delta == 0:
        raise ValidationError("A quantidade não pode ser zero.")

    balance = (
        SaldoEstoque.objects.select_for_update()
        .filter(produto=product)
        .first()
    )
    if balance is None:
        balance = SaldoEstoque.objects.create(produto=product, quantidade=0)

    new_qty = balance.quantidade + quantity_delta
    if new_qty < 0:
        bu = base_unit_for_product_unit(product.unidade)
        raise ValidationError(
            f"Estoque insuficiente para {product.sku}. Disponível: {balance.quantidade} {bu} (unidade base)."
        )

    balance.quantidade = new_qty
    balance.save(update_fields=["quantidade"])

    return MovimentacaoEstoque.objects.create(
        produto=product,
        delta_quantidade=quantity_delta,
        tipo_movimentacao=movement_type,
        ordem_producao=ordem_producao,
        conta_receber=conta_receber,
        conta_pagar=conta_pagar,
        venda_receber_substituta=venda_receber_substituta,
        observacoes=notes,
        criado_por=user,
        quantidade_informada=quantity_input,
        unidade_informada=unit_input if unit_input else None,
    )


apply_movement = aplicar_movimentacao


def _resolve_input_unit(*, raw: str | None, catalog_unit: str) -> str:
    """Unidade informada pelo usuário ou unidade de cadastro do produto."""
    s = (raw or "").strip()
    if not s:
        return catalog_unit
    u = normalize_unit_code(s)
    assert_same_unit_category(u, catalog_unit)
    return u


@transaction.atomic
def executar_producao(
    *,
    produto_id: int,
    quantity_produced,
    lines: list[dict],
    user: User | None = None,
    notes: str = "",
    quantity_produced_unit: str | None = None,
) -> OrdemProducao:
    """
    lines: [{"component": <id>, "quantity_consumed": <decimal>, "quantity_consumed_unit": <opcional>}, ...]
    Baixa insumos e entra produto acabado na mesma transação.
    """
    product = Produto.objects.select_for_update().get(pk=produto_id)
    if product.tipo_produto != Produto.TipoProduto.FABRICADO:
        raise ValidationError("Apenas produtos do tipo fabricado podem ser produzidos.")

    qty_out = _to_decimal(quantity_produced)
    if qty_out <= 0:
        raise ValidationError("Quantidade produzida deve ser maior que zero.")

    if not lines:
        raise ValidationError("Informe ao menos um insumo consumido.")

    unit_out = _resolve_input_unit(raw=quantity_produced_unit, catalog_unit=product.unidade)
    qty_out_base = quantity_to_base(qty_out, unit_out)

    run = OrdemProducao.objects.create(
        produto=product,
        quantidade_produzida=qty_out_base,
        observacoes=notes or "",
        criado_por=user,
    )

    for row in lines:
        comp_id = row.get("component")
        q_cons = _to_decimal(row.get("quantity_consumed"))
        if comp_id is None:
            raise ValidationError("Cada linha deve informar o insumo.")
        if q_cons <= 0:
            raise ValidationError("Quantidade consumida deve ser maior que zero.")

        component = Produto.objects.select_for_update().get(pk=comp_id)
        if component.pk == product.pk:
            raise ValidationError("Insumo não pode ser o próprio produto fabricado.")

        unit_cons = _resolve_input_unit(
            raw=row.get("quantity_consumed_unit"),
            catalog_unit=component.unidade,
        )
        q_cons_base = quantity_to_base(q_cons, unit_cons)

        aplicar_movimentacao(
            product=component,
            quantity_delta=-q_cons_base,
            movement_type=MovimentacaoEstoque.TipoMovimentacao.CONSUMO_PRODUCAO,
            user=user,
            ordem_producao=run,
            notes="",
            quantity_input=q_cons,
            unit_input=unit_cons,
        )
        LinhaOrdemProducao.objects.create(
            ordem=run,
            insumo=component,
            quantidade_consumida=q_cons_base,
        )

    aplicar_movimentacao(
        product=product,
        quantity_delta=qty_out_base,
        movement_type=MovimentacaoEstoque.TipoMovimentacao.ENTRADA_PRODUCAO,
        user=user,
        ordem_producao=run,
        notes="",
        quantity_input=qty_out,
        unit_input=unit_out,
    )

    return run


execute_production = executar_producao

_TIPO_ESTORNO_PRODUCAO = {
    MovimentacaoEstoque.TipoMovimentacao.ENTRADA_PRODUCAO: (
        MovimentacaoEstoque.TipoMovimentacao.ESTORNO_ENTRADA_PRODUCAO
    ),
    MovimentacaoEstoque.TipoMovimentacao.CONSUMO_PRODUCAO: (
        MovimentacaoEstoque.TipoMovimentacao.ESTORNO_CONSUMO_PRODUCAO
    ),
}


@transaction.atomic
def cancelar_ordem_producao(
    *,
    ordem: OrdemProducao,
    user: User | None = None,
) -> OrdemProducao:
    """
    Estorna movimentações de produção da ordem e marca a ordem como cancelada.
    Ordem dos estornos: entrada do acabado primeiro, depois consumos de insumo.
    """
    ordem = OrdemProducao.objects.select_for_update().get(pk=ordem.pk)
    if ordem.cancelada_em is not None:
        raise ValidationError("Esta ordem de produção já foi cancelada.")

    movs = (
        MovimentacaoEstoque.objects.select_for_update()
        .filter(
            ordem_producao=ordem,
            producao_substituta=False,
            tipo_movimentacao__in=[
                MovimentacaoEstoque.TipoMovimentacao.ENTRADA_PRODUCAO,
                MovimentacaoEstoque.TipoMovimentacao.CONSUMO_PRODUCAO,
            ],
        )
        .select_related("produto")
        .order_by(
            Case(
                When(
                    tipo_movimentacao=MovimentacaoEstoque.TipoMovimentacao.ENTRADA_PRODUCAO,
                    then=Value(0),
                ),
                default=Value(1),
                output_field=IntegerField(),
            ),
            "id",
        )
    )
    if not movs.exists():
        raise ValidationError("Ordem sem movimentações de estoque para estornar.")

    for m in movs:
        tipo_estorno = _TIPO_ESTORNO_PRODUCAO.get(m.tipo_movimentacao)
        if tipo_estorno is None:
            raise ValidationError("Tipo de movimentação de produção inválido para estorno.")
        aplicar_movimentacao(
            product=m.produto,
            quantity_delta=-m.delta_quantidade,
            movement_type=tipo_estorno,
            user=user,
            ordem_producao=ordem,
            notes=f"Estorno produção #{ordem.pk}",
            quantity_input=m.quantidade_informada,
            unit_input=m.unidade_informada,
        )
        m.producao_substituta = True
        m.save(update_fields=["producao_substituta"])

    ordem.cancelada_em = timezone.now()
    ordem.cancelada_por = user
    ordem.save(update_fields=["cancelada_em", "cancelada_por"])
    return ordem


cancel_production_run = cancelar_ordem_producao


@transaction.atomic
def reverter_movimentacoes_venda_receber_ativas(
    *,
    receivable: ContaReceber,
    user: User | None = None,
) -> None:
    """Desfaz saídas RECEIVABLE_SALE ativas do título; grava ESTORNO_VENDA_RECEBER."""
    ContaReceber.objects.select_for_update().filter(pk=receivable.pk).first()
    qs = (
        MovimentacaoEstoque.objects.select_for_update()
        .filter(
            conta_receber=receivable,
            tipo_movimentacao=MovimentacaoEstoque.TipoMovimentacao.VENDA_RECEBER,
            venda_receber_substituta=False,
        )
        .select_related("produto")
        .order_by("id")
    )
    for m in qs:
        aplicar_movimentacao(
            product=m.produto,
            quantity_delta=-m.delta_quantidade,
            movement_type=MovimentacaoEstoque.TipoMovimentacao.ESTORNO_VENDA_RECEBER,
            user=user,
            conta_receber=receivable,
            notes=f"Estorno venda (título #{receivable.pk})",
            quantity_input=m.quantidade_informada,
            unit_input=m.unidade_informada,
        )
        m.venda_receber_substituta = True
        m.save(update_fields=["venda_receber_substituta"])


revert_active_receivable_sale_movements = reverter_movimentacoes_venda_receber_ativas


@transaction.atomic
def sincronizar_estoque_conta_receber(
    *,
    receivable: ContaReceber,
    user: User | None = None,
) -> None:
    """Estorna saídas anteriores e baixa estoque conforme linhas atuais do título."""
    ContaReceber.objects.select_for_update().filter(pk=receivable.pk).first()
    receivable.refresh_from_db()
    reverter_movimentacoes_venda_receber_ativas(receivable=receivable, user=user)
    if receivable.situacao == ContaReceber.Situacao.CANCELADO:
        return
    lines = list(
        LinhaContaReceber.objects.filter(conta_receber_id=receivable.pk, produto_id__isnull=False)
        .select_related("produto")
        .order_by("produto_id", "id")
    )
    for line in lines:
        product = line.produto
        product = Produto.objects.select_for_update().get(pk=product.pk)
        unit_line = normalize_unit_code(line.unidade)
        assert_same_unit_category(unit_line, product.unidade)
        q_base = quantity_to_base(line.quantidade, unit_line)
        aplicar_movimentacao(
            product=product,
            quantity_delta=-q_base,
            movement_type=MovimentacaoEstoque.TipoMovimentacao.VENDA_RECEBER,
            user=user,
            conta_receber=receivable,
            notes=f"Conta a receber #{receivable.pk}",
            quantity_input=line.quantidade,
            unit_input=unit_line,
        )


sync_account_receivable_stock = sincronizar_estoque_conta_receber


@transaction.atomic
def registrar_entrada_compra(
    *,
    fornecedor: Fornecedor | None,
    descricao: str,
    vencimento,
    observacoes: str = "",
    linhas: list[dict],
    user: User | None = None,
) -> dict:
    """
    Registra entrada de estoque (vários produtos), gera uma conta a pagar e vincula movimentos.

    Cada item em ``linhas``: produto (id), quantidade, unidade (opcional), custo_unitario (opcional).
    """
    if not linhas:
        raise ValidationError("Informe ao menos uma linha com produto e quantidade.")

    payable = ContaPagar.objects.create(
        fornecedor=fornecedor,
        descricao=descricao.strip(),
        valor=Decimal("0"),
        vencimento=vencimento,
        observacoes=(observacoes or "").strip(),
        criado_por=user,
    )

    total = Decimal("0")
    movements: list[MovimentacaoEstoque] = []
    payable_lines: list[LinhaContaPagar] = []

    for idx, row in enumerate(linhas):
        line_no = idx + 1
        produto_id = row.get("produto")
        if produto_id is None:
            raise ValidationError(f"Linha {line_no}: selecione o produto.")

        product = Produto.objects.select_for_update().get(pk=produto_id)
        if not product.ativo:
            raise ValidationError(f"Linha {line_no}: produto inativo.")
        if product.tipo_produto != Produto.TipoProduto.COMPRADO:
            raise ValidationError(
                f"Linha {line_no}: apenas produtos comprados podem entrar por compra."
            )

        qty = _to_decimal(row.get("quantidade"))
        if qty <= 0:
            raise ValidationError(f"Linha {line_no}: quantidade deve ser maior que zero.")

        unit_in = _resolve_input_unit(raw=row.get("unidade"), catalog_unit=product.unidade)

        custo_raw = row.get("custo_unitario")
        if custo_raw is None or str(custo_raw).strip() == "":
            custo = product.custo_aquisicao
        else:
            custo = quantizar_moeda(custo_raw)
        if custo <= 0:
            raise ValidationError(
                f"Linha {line_no}: informe custo de aquisição no produto ou na linha."
            )

        line_total = calcular_total_linha_compra(
            quantidade=qty,
            unidade=unit_in,
            produto=product,
            custo_unitario=custo,
        )
        total += line_total

        delta = quantity_to_base(qty, unit_in)
        movement = aplicar_movimentacao(
            product=product,
            quantity_delta=delta,
            movement_type=MovimentacaoEstoque.TipoMovimentacao.ENTRADA_COMPRA,
            user=user,
            conta_pagar=payable,
            notes=f"Entrada compra — conta a pagar #{payable.pk}",
            quantity_input=qty,
            unit_input=unit_in,
        )
        movements.append(movement)

        payable_lines.append(
            LinhaContaPagar.objects.create(
                conta_pagar=payable,
                produto=product,
                quantidade=qty,
                unidade=unit_in,
                custo_unitario=custo,
                total_linha=line_total,
            )
        )

    payable.valor = quantizar_moeda(total)
    payable.save(update_fields=["valor", "atualizado_em"])

    return {
        "conta_pagar": payable,
        "linhas": payable_lines,
        "movimentacoes": movements,
    }


register_purchase_entry = registrar_entrada_compra


@transaction.atomic
def reservar_estoque(*, produto: Produto, quantidade: Decimal) -> None:
    """Reserva quantidade do saldo disponível (não altera saldo físico)."""
    if quantidade <= 0:
        raise ValidationError("Quantidade a reservar deve ser positiva.")
    saldo, _ = SaldoEstoque.objects.select_for_update().get_or_create(
        produto=produto,
        defaults={"quantidade": Decimal("0")},
    )
    if saldo.disponivel < quantidade:
        raise ValidationError(
            f"Estoque indisponível. Disponível: {saldo.disponivel}; solicitado: {quantidade}."
        )
    saldo.quantidade_reservada += quantidade
    saldo.save(update_fields=["quantidade_reservada"])


@transaction.atomic
def liberar_reserva(*, produto: Produto, quantidade: Decimal) -> None:
    """Libera parte da reserva (não pode ficar negativa)."""
    if quantidade <= 0:
        raise ValidationError("Quantidade a liberar deve ser positiva.")
    saldo = SaldoEstoque.objects.select_for_update().get(produto=produto)
    saldo.quantidade_reservada = max(Decimal("0"), saldo.quantidade_reservada - quantidade)
    saldo.save(update_fields=["quantidade_reservada"])
