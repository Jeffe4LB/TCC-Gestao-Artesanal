from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import HasCapability

from stock.services import revert_active_receivable_sale_movements

from .filters import AccountPayableFilter, AccountReceivableFilter
from .models import AccountPayable, AccountReceivable
from .serializers import (
    AccountPayableSerializer,
    AccountReceivableSerializer,
    PayableAlertSerializer,
    ReceivableAlertSerializer,
)


class AccountPayableViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = "finance"
    queryset = AccountPayable.objects.select_related("supplier", "created_by").all()
    serializer_class = AccountPayableSerializer
    filterset_class = AccountPayableFilter
    search_fields = ["description", "notes"]
    ordering_fields = ["due_date", "amount", "created_at", "id"]
    ordering = ["due_date"]

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(created_by=user)


class AccountReceivableViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = "finance"
    queryset = (
        AccountReceivable.objects.select_related("customer", "created_by")
        .prefetch_related("lines__product")
        .all()
    )
    serializer_class = AccountReceivableSerializer
    filterset_class = AccountReceivableFilter
    search_fields = ["description", "notes"]
    ordering_fields = ["due_date", "amount", "created_at", "id"]
    ordering = ["due_date"]

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(created_by=user)

    def perform_destroy(self, instance):
        user = self.request.user if self.request.user.is_authenticated else None
        try:
            with transaction.atomic():
                revert_active_receivable_sale_movements(receivable=instance, user=user)
                instance.delete()
        except DjangoValidationError as exc:
            raise DRFValidationError(detail=list(exc.messages)) from exc


class CashFlowView(APIView):
    """
    Fluxo de caixa pelo período: entradas e saídas pela **data efetiva**
    (recebido em / pago em), apenas lançamentos com status recebido/pago.
    Query: ?from=YYYY-MM-DD&to=YYYY-MM-DD
    """

    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = "finance"

    def get(self, request):
        from_s = request.query_params.get("from")
        to_s = request.query_params.get("to")
        if not from_s or not to_s:
            return Response(
                {"detail": "Informe os parâmetros from e to (YYYY-MM-DD)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        date_from = parse_date(from_s)
        date_to = parse_date(to_s)
        if not date_from or not date_to:
            return Response(
                {"detail": "Datas inválidas. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if date_from > date_to:
            return Response(
                {"detail": "from não pode ser maior que to."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        inflows = AccountReceivable.objects.filter(
            status=AccountReceivable.Status.PAID,
            received_at__gte=date_from,
            received_at__lte=date_to,
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

        outflows = AccountPayable.objects.filter(
            status=AccountPayable.Status.PAID,
            paid_at__gte=date_from,
            paid_at__lte=date_to,
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

        net = inflows - outflows

        return Response(
            {
                "from": date_from.isoformat(),
                "to": date_to.isoformat(),
                "inflows": str(inflows),
                "outflows": str(outflows),
                "net": str(net),
            }
        )


class FinanceAlertView(APIView):
    """
    Vencidas + a vencer em X dias (apenas em aberto).
    Query: ?days_ahead=7 (padrão 7)
    """

    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = "finance"

    def get(self, request):
        try:
            days_ahead = int(request.query_params.get("days_ahead", 7))
        except (TypeError, ValueError):
            days_ahead = 7
        if days_ahead < 0:
            days_ahead = 0

        today = timezone.now().date()
        until = today + timedelta(days=days_ahead)

        overdue_payables = (
            AccountPayable.objects.filter(
                status=AccountPayable.Status.OPEN,
                due_date__lt=today,
            )
            .select_related("supplier")
            .order_by("due_date")[:500]
        )
        overdue_receivables = (
            AccountReceivable.objects.filter(
                status=AccountReceivable.Status.OPEN,
                due_date__lt=today,
            )
            .select_related("customer")
            .order_by("due_date")[:500]
        )

        due_soon_payables = (
            AccountPayable.objects.filter(
                status=AccountPayable.Status.OPEN,
                due_date__gte=today,
                due_date__lte=until,
            )
            .select_related("supplier")
            .order_by("due_date")[:500]
        )
        due_soon_receivables = (
            AccountReceivable.objects.filter(
                status=AccountReceivable.Status.OPEN,
                due_date__gte=today,
                due_date__lte=until,
            )
            .select_related("customer")
            .order_by("due_date")[:500]
        )

        return Response(
            {
                "today": today.isoformat(),
                "days_ahead": days_ahead,
                "until": until.isoformat(),
                "overdue": {
                    "payables": PayableAlertSerializer(overdue_payables, many=True).data,
                    "receivables": ReceivableAlertSerializer(overdue_receivables, many=True).data,
                },
                "due_soon": {
                    "payables": PayableAlertSerializer(due_soon_payables, many=True).data,
                    "receivables": ReceivableAlertSerializer(due_soon_receivables, many=True).data,
                },
            }
        )
