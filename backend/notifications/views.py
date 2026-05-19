from datetime import timedelta
from decimal import Decimal

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.capabilities import user_has_capability
from core.permissions import HasCapability

from .models import UserNotification
from .serializers import UserNotificationCreateSerializer, UserNotificationSerializer
from .services import build_notification_summary


class NotificationSummaryView(APIView):
    """
    Resumo para dashboard: estoque abaixo do mínimo + totais de alertas financeiros.
    Query: ?days_ahead=7 (para faixa "a vencer")
    """

    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = "dashboard"

    def get(self, request):
        try:
            days_ahead = int(request.query_params.get("days_ahead", 7))
        except (TypeError, ValueError):
            days_ahead = 7
        if days_ahead < 0:
            days_ahead = 0

        try:
            preview = int(request.query_params.get("stock_preview", 10))
        except (TypeError, ValueError):
            preview = 10
        preview = max(1, min(preview, 50))

        data = build_notification_summary(days_ahead=days_ahead, stock_preview_limit=preview)
        if not user_has_capability(request.user, "stock_read"):
            data["stock_below_minimum"] = {"count": 0, "preview": []}
        if not user_has_capability(request.user, "finance"):
            today = timezone.now().date()
            until = today + timedelta(days=days_ahead)
            data["finance"] = {
                "today": today.isoformat(),
                "until": until.isoformat(),
                "days_ahead": days_ahead,
                "overdue": {
                    "payables_count": 0,
                    "payables_total": str(Decimal("0")),
                    "receivables_count": 0,
                    "receivables_total": str(Decimal("0")),
                },
                "due_soon": {"payables_count": 0, "receivables_count": 0},
            }
        return Response(data)


class UserNotificationPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class UserNotificationListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = UserNotificationPagination

    def get_serializer_class(self):
        if self.request.method == "POST":
            return UserNotificationCreateSerializer
        return UserNotificationSerializer

    def get_queryset(self):
        qs = UserNotification.objects.filter(user=self.request.user)
        unread = self.request.query_params.get("unread", "").lower()
        if unread in ("1", "true", "yes"):
            qs = qs.filter(read_at__isnull=True)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserNotificationMarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        n = get_object_or_404(UserNotification, pk=pk, user=request.user)
        if n.read_at is None:
            n.read_at = timezone.now()
            n.save(update_fields=["read_at"])
        return Response(UserNotificationSerializer(n).data)


class UserNotificationMarkAllReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        UserNotification.objects.filter(user=request.user, read_at__isnull=True).update(
            read_at=timezone.now()
        )
        return Response({"detail": "Todas marcadas como lidas."})
