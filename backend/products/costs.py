"""
Custo unitário e preço de venda (Fase 2).

Modelo de custo de aquisição (produto comprado):
  - ``purchase_unit_cost``: custo de aquisição por **1 unidade de cadastro**
    do produto (mesma unidade do campo ``Product.unit``).

Custo fabricado (BOM):
  - ``unit_cost`` = soma, para cada linha da receita, de
    ``quantity_per_unit × component.unit_cost``,
    onde ``quantity_per_unit`` está na **unidade de cadastro do insumo**
    e ``component.unit_cost`` é **R$ por 1 unidade de cadastro** desse insumo.

Arredondamento monetário: 2 casas decimais (``ROUND_HALF_UP``).
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

MONEY_QUANT = Decimal("0.01")


def quant_money(value: Decimal | str | float | int) -> Decimal:
    return Decimal(str(value)).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def bom_unit_cost_sum(product: "Product") -> Decimal:
    """Custo de 1 unidade fabricada a partir da receita (0 se não houver receita)."""
    from products.models import Product as ProductModel
    from stock.models import Recipe

    if product.product_type != ProductModel.ProductType.MANUFACTURED:
        return quant_money(product.unit_cost)

    recipe = (
        Recipe.objects.filter(product_id=product.pk)
        .prefetch_related("lines__component")
        .first()
    )
    if not recipe:
        return Decimal("0")

    total = Decimal("0")
    for line in recipe.lines.all():
        comp = line.component
        total += Decimal(str(line.quantity_per_unit)) * Decimal(str(comp.unit_cost))
    return quant_money(total)


def bump_manufactured_using_component(component_id: int) -> None:
    """Recalcula custo dos fabricados que usam este insumo."""
    from products.models import Product as ProductModel
    from stock.models import RecipeLine

    product_ids = (
        RecipeLine.objects.filter(component_id=component_id)
        .values_list("recipe__product_id", flat=True)
        .distinct()
    )
    for pid in product_ids:
        p = ProductModel.objects.get(pk=pid)
        if p.product_type != ProductModel.ProductType.MANUFACTURED:
            continue
        uc = bom_unit_cost_sum(p)
        ProductModel.objects.filter(pk=pid).update(unit_cost=uc)


def finalize_product_unit_cost(product: "Product") -> None:
    """
    Atualiza ``unit_cost`` após salvar produto ou alterar receita.
    Produto comprado: ``unit_cost = purchase_unit_cost`` (quantizado).
    Fabricado: ``unit_cost`` pela soma da BOM.
    """
    from products.models import Product as ProductModel

    product.refresh_from_db()
    if product.product_type == ProductModel.ProductType.PURCHASED:
        uc = quant_money(product.purchase_unit_cost)
        ProductModel.objects.filter(pk=product.pk).update(unit_cost=uc)
        bump_manufactured_using_component(product.pk)
    else:
        uc = bom_unit_cost_sum(product)
        ProductModel.objects.filter(pk=product.pk).update(unit_cost=uc)
