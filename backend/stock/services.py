from decimal import Decimal, InvalidOperation

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction

from core.units import (
    assert_same_unit_category,
    base_unit_for_product_unit,
    normalize_unit_code,
    quantity_to_base,
)

from finance.models import AccountReceivable, AccountReceivableLine
from products.models import Product

from .models import (
    ProductionRun,
    ProductionRunLine,
    StockBalance,
    StockMovement,
)

User = get_user_model()


def _to_decimal(value) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValidationError("Quantidade inválida.") from exc


@transaction.atomic
def apply_movement(
    *,
    product: Product,
    quantity_delta: Decimal,
    movement_type: str,
    user: User | None = None,
    production_run=None,
    account_receivable: AccountReceivable | None = None,
    receivable_sale_superseded: bool = False,
    notes: str = "",
    quantity_input: Decimal | None = None,
    unit_input: str | None = None,
) -> StockMovement:
    """
    Atualiza saldo (com lock) e grava movimento.
    ``quantity_delta`` deve estar na **unidade base** (KG, L ou UN).
    """
    if quantity_delta == 0:
        raise ValidationError("A quantidade não pode ser zero.")

    balance = (
        StockBalance.objects.select_for_update()
        .filter(product=product)
        .first()
    )
    if balance is None:
        balance = StockBalance.objects.create(product=product, quantity=0)

    new_qty = balance.quantity + quantity_delta
    if new_qty < 0:
        bu = base_unit_for_product_unit(product.unit)
        raise ValidationError(
            f"Estoque insuficiente para {product.sku}. Disponível: {balance.quantity} {bu} (base)."
        )

    balance.quantity = new_qty
    balance.save(update_fields=["quantity"])

    return StockMovement.objects.create(
        product=product,
        quantity_delta=quantity_delta,
        movement_type=movement_type,
        production_run=production_run,
        account_receivable=account_receivable,
        receivable_sale_superseded=receivable_sale_superseded,
        notes=notes,
        created_by=user,
        quantity_input=quantity_input,
        unit_input=unit_input if unit_input else None,
    )


def _resolve_input_unit(*, raw: str | None, catalog_unit: str) -> str:
    """Unidade informada pelo usuário ou unidade de cadastro do produto."""
    s = (raw or "").strip()
    if not s:
        return catalog_unit
    u = normalize_unit_code(s)
    assert_same_unit_category(u, catalog_unit)
    return u


@transaction.atomic
def execute_production(
    *,
    product_id: int,
    quantity_produced,
    lines: list[dict],
    user: User | None = None,
    notes: str = "",
    quantity_produced_unit: str | None = None,
) -> ProductionRun:
    """
    lines: [{"component": <id>, "quantity_consumed": <decimal>, "quantity_consumed_unit": <opcional>}, ...]
    Baixa insumos e entra produto acabado na mesma transação.
    Quantidades são interpretadas na unidade informada (mesma categoria da unidade de cadastro do produto).
    """
    product = Product.objects.select_for_update().get(pk=product_id)
    if product.product_type != Product.ProductType.MANUFACTURED:
        raise ValidationError("Apenas produtos do tipo fabricado podem ser produzidos.")

    qty_out = _to_decimal(quantity_produced)
    if qty_out <= 0:
        raise ValidationError("Quantidade produzida deve ser maior que zero.")

    if not lines:
        raise ValidationError("Informe ao menos um insumo consumido.")

    unit_out = _resolve_input_unit(raw=quantity_produced_unit, catalog_unit=product.unit)
    qty_out_base = quantity_to_base(qty_out, unit_out)

    run = ProductionRun.objects.create(
        product=product,
        quantity_produced=qty_out_base,
        notes=notes or "",
        created_by=user,
    )

    for row in lines:
        comp_id = row.get("component")
        q_cons = _to_decimal(row.get("quantity_consumed"))
        if comp_id is None:
            raise ValidationError("Cada linha deve ter 'component' (id do insumo).")
        if q_cons <= 0:
            raise ValidationError("Quantidade consumida deve ser maior que zero.")

        component = Product.objects.select_for_update().get(pk=comp_id)
        if component.pk == product.pk:
            raise ValidationError("Insumo não pode ser o próprio produto fabricado.")

        unit_cons = _resolve_input_unit(
            raw=row.get("quantity_consumed_unit"),
            catalog_unit=component.unit,
        )
        q_cons_base = quantity_to_base(q_cons, unit_cons)

        apply_movement(
            product=component,
            quantity_delta=-q_cons_base,
            movement_type=StockMovement.MovementType.PRODUCTION_CONSUMPTION,
            user=user,
            production_run=run,
            notes="",
            quantity_input=q_cons,
            unit_input=unit_cons,
        )
        ProductionRunLine.objects.create(
            run=run,
            component=component,
            quantity_consumed=q_cons_base,
        )

    apply_movement(
        product=product,
        quantity_delta=qty_out_base,
        movement_type=StockMovement.MovementType.PRODUCTION_OUTPUT,
        user=user,
        production_run=run,
        notes="",
        quantity_input=qty_out,
        unit_input=unit_out,
    )

    return run


@transaction.atomic
def revert_active_receivable_sale_movements(
    *,
    receivable: AccountReceivable,
    user: User | None = None,
) -> None:
    """
    Desfaz no estoque as saídas ``RECEIVABLE_SALE`` deste título que ainda estão ativas
    (não estornadas por edição anterior). Grava movimentos ``RECEIVABLE_SALE_REVERSAL``.
    """
    AccountReceivable.objects.select_for_update().filter(pk=receivable.pk).first()
    qs = (
        StockMovement.objects.select_for_update()
        .filter(
            account_receivable=receivable,
            movement_type=StockMovement.MovementType.RECEIVABLE_SALE,
            receivable_sale_superseded=False,
        )
        .select_related("product")
        .order_by("id")
    )
    for m in qs:
        apply_movement(
            product=m.product,
            quantity_delta=-m.quantity_delta,
            movement_type=StockMovement.MovementType.RECEIVABLE_SALE_REVERSAL,
            user=user,
            account_receivable=receivable,
            notes=f"Estorno venda (título #{receivable.pk})",
            quantity_input=m.quantity_input,
            unit_input=m.unit_input,
        )
        m.receivable_sale_superseded = True
        m.save(update_fields=["receivable_sale_superseded"])


@transaction.atomic
def sync_account_receivable_stock(
    *,
    receivable: AccountReceivable,
    user: User | None = None,
) -> None:
    """
    Alinha o estoque com as linhas atuais do título: estorna saídas anteriores e,
    se status não for cancelado, baixa novamente conforme cada linha com produto.
    """
    AccountReceivable.objects.select_for_update().filter(pk=receivable.pk).first()
    receivable.refresh_from_db()
    revert_active_receivable_sale_movements(receivable=receivable, user=user)
    if receivable.status == AccountReceivable.Status.CANCELLED:
        return
    lines = list(
        AccountReceivableLine.objects.filter(receivable_id=receivable.pk, product_id__isnull=False)
        .select_related("product")
        .order_by("product_id", "id")
    )
    for line in lines:
        product = line.product
        product = Product.objects.select_for_update().get(pk=product.pk)
        unit_line = normalize_unit_code(line.unit)
        assert_same_unit_category(unit_line, product.unit)
        q_base = quantity_to_base(line.quantity, unit_line)
        apply_movement(
            product=product,
            quantity_delta=-q_base,
            movement_type=StockMovement.MovementType.RECEIVABLE_SALE,
            user=user,
            account_receivable=receivable,
            notes=f"Conta a receber #{receivable.pk}",
            quantity_input=line.quantity,
            unit_input=unit_line,
        )
