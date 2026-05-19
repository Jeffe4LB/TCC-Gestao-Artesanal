from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from finance.models import AccountPayable, AccountReceivable
from reports.services import low_stock_queryset


def build_notification_summary(*, days_ahead: int = 7, stock_preview_limit: int = 10) -> dict:
    """Agrega alertas de estoque + financeiro para o painel (MVP)."""
    today = timezone.now().date()
    until = today + timedelta(days=days_ahead)

    low = low_stock_queryset()
    stock_preview = []
    for b in low[:stock_preview_limit]:
        p = b.product
        stock_preview.append(
            {
                "sku": p.sku,
                "name": p.name,
                "min_stock": str(p.min_stock),
                "current_quantity": str(b.quantity),
                "gap": str(b.gap),
            }
        )

    op = AccountPayable.objects.filter(
        status=AccountPayable.Status.OPEN,
        due_date__lt=today,
    )
    ore = AccountReceivable.objects.filter(
        status=AccountReceivable.Status.OPEN,
        due_date__lt=today,
    )
    overdue = {
        "payables_count": op.count(),
        "payables_total": str(op.aggregate(t=Sum("amount"))["t"] or Decimal("0")),
        "receivables_count": ore.count(),
        "receivables_total": str(ore.aggregate(t=Sum("amount"))["t"] or Decimal("0")),
    }

    dsp = AccountPayable.objects.filter(
        status=AccountPayable.Status.OPEN,
        due_date__gte=today,
        due_date__lte=until,
    )
    dsr = AccountReceivable.objects.filter(
        status=AccountReceivable.Status.OPEN,
        due_date__gte=today,
        due_date__lte=until,
    )
    due_soon = {
        "payables_count": dsp.count(),
        "receivables_count": dsr.count(),
    }

    return {
        "generated_at": timezone.now().isoformat(),
        "stock_below_minimum": {
            "count": low.count(),
            "preview": stock_preview,
        },
        "finance": {
            "today": today.isoformat(),
            "until": until.isoformat(),
            "days_ahead": days_ahead,
            "overdue": overdue,
            "due_soon": due_soon,
        },
    }
