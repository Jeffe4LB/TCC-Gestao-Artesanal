from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import DecimalField, ExpressionWrapper, F, Sum

from finance.models import AccountPayable, AccountReceivable, AccountReceivableLine
from stock.models import StockBalance


def _money_q2(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def stock_position_queryset():
    return (
        StockBalance.objects.select_related("product", "product__category")
        .filter(product__is_active=True)
        .order_by("product__sku")
    )


def low_stock_queryset():
    return (
        StockBalance.objects.filter(
            product__is_active=True,
            product__min_stock__gt=0,
            quantity__lte=F("product__min_stock"),
        )
        .select_related("product", "product__category")
        .annotate(gap=F("product__min_stock") - F("quantity"))
        .order_by("-gap", "product__sku")
    )


def finance_open_totals():
    payables = AccountPayable.objects.filter(status=AccountPayable.Status.OPEN)
    receivables = AccountReceivable.objects.filter(status=AccountReceivable.Status.OPEN)
    return {
        "payables_count": payables.count(),
        "payables_total": payables.aggregate(t=Sum("amount"))["t"] or Decimal("0"),
        "receivables_count": receivables.count(),
        "receivables_total": receivables.aggregate(t=Sum("amount"))["t"] or Decimal("0"),
    }


def cash_flow_totals(date_from, date_to):
    inflows = AccountReceivable.objects.filter(
        status=AccountReceivable.Status.PAID,
        received_at__gte=date_from,
        received_at__lte=date_to,
    ).aggregate(t=Sum("amount"))["t"] or Decimal("0")
    outflows = AccountPayable.objects.filter(
        status=AccountPayable.Status.PAID,
        paid_at__gte=date_from,
        paid_at__lte=date_to,
    ).aggregate(t=Sum("amount"))["t"] or Decimal("0")
    return inflows, outflows, inflows - outflows


def aging_buckets(model_cls, today):
    """Agrupa lançamentos em aberto por faixa de vencimento."""
    open_status = (
        AccountPayable.Status.OPEN
        if model_cls is AccountPayable
        else AccountReceivable.Status.OPEN
    )
    qs = model_cls.objects.filter(status=open_status)
    until_7 = today + timedelta(days=7)
    until_30 = today + timedelta(days=30)

    overdue = qs.filter(due_date__lt=today)
    due_0_7 = qs.filter(due_date__gte=today, due_date__lte=until_7)
    due_8_30 = qs.filter(due_date__gt=until_7, due_date__lte=until_30)
    due_future = qs.filter(due_date__gt=until_30)

    def agg(q):
        return {
            "count": q.count(),
            "total": q.aggregate(t=Sum("amount"))["t"] or Decimal("0"),
        }

    return {
        "overdue": agg(overdue),
        "due_next_7_days": agg(due_0_7),
        "due_8_to_30_days": agg(due_8_30),
        "due_after_30_days": agg(due_future),
    }


def revenue_by_product_rows(date_from, date_to, customer_id=None, category_id=None):
    """
    Agrega linhas de contas a receber por produto (data de emissão do título).

    - Faturamento: soma dos ``line_total`` (preço efetivo da venda na linha).
    - Custo: ``Sum(quantity * product.unit_cost)`` com custo **atual** do cadastro.
    - Lucro (margem em R$): faturamento − custo; ``margin_percent`` = lucro / faturamento × 100.
    """
    qs = AccountReceivableLine.objects.filter(
        receivable__issue_date__gte=date_from,
        receivable__issue_date__lte=date_to,
        receivable__status__in=(
            AccountReceivable.Status.OPEN,
            AccountReceivable.Status.PAID,
        ),
        product_id__isnull=False,
    )
    if customer_id:
        qs = qs.filter(receivable__customer_id=customer_id)
    if category_id:
        qs = qs.filter(product__category_id=category_id)

    cost_expr = ExpressionWrapper(
        F("quantity") * F("product__unit_cost"),
        output_field=DecimalField(max_digits=24, decimal_places=6),
    )

    agg = (
        qs.values(
            "product_id",
            "product__sku",
            "product__name",
            "product__category__name",
        )
        .annotate(
            quantity_total=Sum("quantity"),
            sales_total=Sum("line_total"),
            cost_total=Sum(cost_expr),
        )
        .order_by("product__sku")
    )

    rows = []
    for row in agg:
        qty = row["quantity_total"] or Decimal("0")
        sales = _money_q2(row["sales_total"] or Decimal("0"))
        cost = _money_q2(row["cost_total"] or Decimal("0"))
        profit = _money_q2(sales - cost)
        margin_pct = (
            (profit / sales * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if sales > 0
            else Decimal("0")
        )
        rows.append(
            {
                "product_id": row["product_id"],
                "sku": row["product__sku"] or "",
                "name": row["product__name"] or "",
                "category": row["product__category__name"] or "",
                "quantity_total": qty,
                "sales_total": sales,
                "cost_total": cost,
                "profit": profit,
                "margin_percent": margin_pct,
            }
        )
    return rows
