"""
Custo unitário e preço de venda.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

MONEY_QUANT = Decimal("0.01")


def quant_money(value: Decimal | str | float | int) -> Decimal:
    return Decimal(str(value)).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def soma_custo_receita(produto: "Produto") -> Decimal:
    """Custo de 1 unidade fabricada a partir da receita (0 se não houver receita)."""
    from estoque.models import Receita
    from produtos.models import Produto

    if produto.tipo_produto != Produto.TipoProduto.FABRICADO:
        return quant_money(produto.custo_unitario)

    receita = (
        Receita.objects.filter(produto_id=produto.pk)
        .prefetch_related("linhas__insumo")
        .first()
    )
    if not receita:
        return Decimal("0")

    total = Decimal("0")
    for linha in receita.linhas.all():
        insumo = linha.insumo
        total += Decimal(str(linha.quantidade_por_unidade)) * Decimal(str(insumo.custo_unitario))
    return quant_money(total)


def recalcular_fabricados_que_usam_insumo(insumo_id: int) -> None:
    from estoque.models import LinhaReceita
    from produtos.models import Produto

    produto_ids = (
        LinhaReceita.objects.filter(insumo_id=insumo_id)
        .values_list("receita__produto_id", flat=True)
        .distinct()
    )
    for pid in produto_ids:
        p = Produto.objects.get(pk=pid)
        if p.tipo_produto != Produto.TipoProduto.FABRICADO:
            continue
        uc = soma_custo_receita(p)
        Produto.objects.filter(pk=pid).update(custo_unitario=uc)


def finalizar_custo_unitario_produto(produto: "Produto") -> None:
    from produtos.models import Produto

    produto.refresh_from_db()
    if produto.tipo_produto == Produto.TipoProduto.COMPRADO:
        uc = quant_money(produto.custo_aquisicao)
        Produto.objects.filter(pk=produto.pk).update(custo_unitario=uc)
        recalcular_fabricados_que_usam_insumo(produto.pk)
    else:
        uc = soma_custo_receita(produto)
        Produto.objects.filter(pk=produto.pk).update(custo_unitario=uc)


finalize_product_unit_cost = finalizar_custo_unitario_produto
bom_unit_cost_sum = soma_custo_receita
bump_manufactured_using_component = recalcular_fabricados_que_usam_insumo
