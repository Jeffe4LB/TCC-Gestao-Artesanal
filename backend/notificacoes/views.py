from datetime import timedelta
from decimal import Decimal

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from nucleo.capabilities import usuario_tem_capacidade
from nucleo.pagination import PaginacaoPortugues
from nucleo.permissions import TemCapacidade
from relatorios.utils import parsear_parametro_data

from .models import NotificacaoUsuario
from .serializers import NotificacaoUsuarioCriacaoSerializer, NotificacaoUsuarioSerializer
from .services import montar_resumo_notificacoes


class ResumoNotificacoesView(APIView):
    """
    Resumo para dashboard: estoque abaixo do mínimo + totais de alertas financeiros.
    Query: ?days_ahead=7 (para faixa "a vencer")
    """

    permission_classes = [IsAuthenticated, TemCapacidade]
    required_capability = "painel"

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

        data_de = parsear_parametro_data(request.query_params.get("from"))
        data_ate = parsear_parametro_data(request.query_params.get("to"))
        if data_de and data_ate and data_de > data_ate:
            data_de = None
            data_ate = None

        data = montar_resumo_notificacoes(
            days_ahead=days_ahead,
            stock_preview_limit=preview,
            data_de=data_de,
            data_ate=data_ate,
            usuario=request.user,
        )
        if not usuario_tem_capacidade(request.user, "estoque_leitura"):
            data["estoque_abaixo_minimo"] = {"quantidade": 0, "previa": []}
        if not usuario_tem_capacidade(request.user, "financeiro"):
            today = timezone.now().date()
            until = today + timedelta(days=days_ahead)
            data["financeiro"] = {
                "hoje": today.isoformat(),
                "ate": until.isoformat(),
                "dias_a_frente": days_ahead,
                "vencidos": {
                    "contagem_pagar": 0,
                    "total_pagar": str(Decimal("0")),
                    "contagem_receber": 0,
                    "total_receber": str(Decimal("0")),
                },
                "a_vencer": {"contagem_pagar": 0, "contagem_receber": 0},
            }
        return Response(data)


class NotificacaoUsuarioListaCriacaoView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = PaginacaoPortugues

    def get_serializer_class(self):
        if self.request.method == "POST":
            return NotificacaoUsuarioCriacaoSerializer
        return NotificacaoUsuarioSerializer

    def get_queryset(self):
        qs = NotificacaoUsuario.objects.filter(usuario=self.request.user)
        unread = self.request.query_params.get("unread", "").lower()
        if unread in ("1", "true", "yes"):
            qs = qs.filter(lida_em__isnull=True)
        return qs

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)


class NotificacaoUsuarioMarcarLidaView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        n = get_object_or_404(NotificacaoUsuario, pk=pk, usuario=request.user)
        if n.lida_em is None:
            n.lida_em = timezone.now()
            n.save(update_fields=["lida_em"])
        return Response(NotificacaoUsuarioSerializer(n).data)


class NotificacaoUsuarioMarcarTodasLidasView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        NotificacaoUsuario.objects.filter(usuario=request.user, lida_em__isnull=True).update(
            lida_em=timezone.now()
        )
        return Response({"detail": "Todas marcadas como lidas."})


# Aliases legados (urls)
NotificationSummaryView = ResumoNotificacoesView
UserNotificationListCreateView = NotificacaoUsuarioListaCriacaoView
UserNotificationMarkReadView = NotificacaoUsuarioMarcarLidaView
UserNotificationMarkAllReadView = NotificacaoUsuarioMarcarTodasLidasView
