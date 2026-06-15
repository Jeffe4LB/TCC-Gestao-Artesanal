from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from estoque.services import reverter_movimentacoes_venda_receber_ativas
from nucleo.permissions import TemCapacidade

from .filters import FiltroContaPagar, FiltroContaReceber, FiltroDocumentoFinanceiro
from .models import ContaPagar, ContaReceber, DocumentoFinanceiro
from .serializers import (
    AlertaContaPagarSerializer,
    AlertaContaReceberSerializer,
    ContaPagarSerializer,
    ContaReceberSerializer,
    DocumentoFinanceiroCriacaoSerializer,
    DocumentoFinanceiroSerializer,
    QuitarParcelaSerializer,
)
from .services import (
    SITUACOES_EM_ABERTO_PAGAR,
    SITUACOES_EM_ABERTO_RECEBER,
    cancelar_documento,
    quitar_parcela,
)


class DocumentoFinanceiroViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """Documentos financeiros parcelados (cabeçalho + N parcelas)."""

    permission_classes = [IsAuthenticated, TemCapacidade]
    required_capability = "financeiro"
    queryset = (
        DocumentoFinanceiro.objects.select_related("fornecedor", "cliente", "criado_por")
        .prefetch_related("contas_pagar", "contas_receber")
        .all()
    )
    filterset_class = FiltroDocumentoFinanceiro
    search_fields = ["descricao", "observacoes"]
    ordering_fields = ["data_emissao", "valor_total", "criado_em", "id"]
    ordering = ["-data_emissao", "-id"]

    def get_serializer_class(self):
        if self.action == "create":
            return DocumentoFinanceiroCriacaoSerializer
        return DocumentoFinanceiroSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        documento = serializer.save()
        output = DocumentoFinanceiroSerializer(documento, context=self.get_serializer_context())
        return Response(output.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="cancelar")
    def cancelar(self, request, pk=None):
        documento = self.get_object()
        try:
            documento = cancelar_documento(documento)
        except DjangoValidationError as exc:
            raise DRFValidationError(detail=list(exc.messages)) from exc
        return Response(DocumentoFinanceiroSerializer(documento).data)

    @action(detail=True, methods=["post"], url_path="quitar-parcela")
    def quitar_parcela_action(self, request, pk=None):
        documento = self.get_object()
        body = QuitarParcelaSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        parcela_id = body.validated_data["parcela_id"]
        if documento.tipo == DocumentoFinanceiro.Tipo.PAGAR:
            parcela = documento.contas_pagar.filter(pk=parcela_id).first()
        else:
            parcela = documento.contas_receber.filter(pk=parcela_id).first()
        if parcela is None:
            raise DRFValidationError({"parcela_id": "Parcela não pertence a este documento."})
        try:
            usuario = request.user if request.user.is_authenticated else None
            quitar_parcela(
                parcela=parcela,
                valor_pago=body.validated_data["valor"],
                data_pagamento=body.validated_data["data_pagamento"],
                usuario=usuario,
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(detail=list(exc.messages)) from exc
        documento.refresh_from_db()
        return Response(DocumentoFinanceiroSerializer(documento).data)


class ContaPagarViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, TemCapacidade]
    required_capability = "financeiro"
    queryset = ContaPagar.objects.select_related("fornecedor", "criado_por").all()
    serializer_class = ContaPagarSerializer
    filterset_class = FiltroContaPagar
    search_fields = ["descricao", "observacoes"]
    ordering_fields = ["vencimento", "valor", "criado_em", "id"]
    ordering = ["vencimento"]

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(criado_por=user)


class ContaReceberViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, TemCapacidade]
    required_capability = "financeiro"
    queryset = (
        ContaReceber.objects.select_related("cliente", "criado_por")
        .prefetch_related("linhas__produto")
        .all()
    )
    serializer_class = ContaReceberSerializer
    filterset_class = FiltroContaReceber
    search_fields = ["descricao", "observacoes"]
    ordering_fields = ["vencimento", "valor", "criado_em", "id"]
    ordering = ["vencimento"]

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(criado_por=user)

    def perform_destroy(self, instance):
        user = self.request.user if self.request.user.is_authenticated else None
        try:
            with transaction.atomic():
                reverter_movimentacoes_venda_receber_ativas(receivable=instance, user=user)
                instance.delete()
        except DjangoValidationError as exc:
            raise DRFValidationError(detail=list(exc.messages)) from exc


class FluxoCaixaView(APIView):
    """Fluxo de caixa por data efetiva (recebido em / pago em)."""

    permission_classes = [IsAuthenticated, TemCapacidade]
    required_capability = "financeiro"

    def get(self, request):
        from_s = request.query_params.get("from")
        to_s = request.query_params.get("to")
        if not from_s or not to_s:
            return Response(
                {"detail": "Informe as datas inicial e final (AAAA-MM-DD)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        date_from = parse_date(from_s)
        date_to = parse_date(to_s)
        if not date_from or not date_to:
            return Response(
                {"detail": "Datas inválidas. Use o formato AAAA-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if date_from > date_to:
            return Response(
                {"detail": "A data inicial não pode ser posterior à data final."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        inflows = ContaReceber.objects.filter(
            situacao=ContaReceber.Situacao.RECEBIDO,
            recebido_em__gte=date_from,
            recebido_em__lte=date_to,
        ).aggregate(total=Sum("valor"))["total"] or Decimal("0")

        outflows = ContaPagar.objects.filter(
            situacao=ContaPagar.Situacao.PAGO,
            pago_em__gte=date_from,
            pago_em__lte=date_to,
        ).aggregate(total=Sum("valor"))["total"] or Decimal("0")

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


class AlertasFinanceirosView(APIView):
    """Vencidas + a vencer em X dias (apenas em aberto)."""

    permission_classes = [IsAuthenticated, TemCapacidade]
    required_capability = "financeiro"

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
            ContaPagar.objects.filter(
                situacao__in=SITUACOES_EM_ABERTO_PAGAR,
                vencimento__lt=today,
            )
            .select_related("fornecedor")
            .order_by("vencimento")[:500]
        )
        overdue_receivables = (
            ContaReceber.objects.filter(
                situacao__in=SITUACOES_EM_ABERTO_RECEBER,
                vencimento__lt=today,
            )
            .select_related("cliente")
            .order_by("vencimento")[:500]
        )

        due_soon_payables = (
            ContaPagar.objects.filter(
                situacao__in=SITUACOES_EM_ABERTO_PAGAR,
                vencimento__gte=today,
                vencimento__lte=until,
            )
            .select_related("fornecedor")
            .order_by("vencimento")[:500]
        )
        due_soon_receivables = (
            ContaReceber.objects.filter(
                situacao__in=SITUACOES_EM_ABERTO_RECEBER,
                vencimento__gte=today,
                vencimento__lte=until,
            )
            .select_related("cliente")
            .order_by("vencimento")[:500]
        )

        return Response(
            {
                "today": today.isoformat(),
                "days_ahead": days_ahead,
                "until": until.isoformat(),
                "overdue": {
                    "payables": AlertaContaPagarSerializer(overdue_payables, many=True).data,
                    "receivables": AlertaContaReceberSerializer(overdue_receivables, many=True).data,
                },
                "due_soon": {
                    "payables": AlertaContaPagarSerializer(due_soon_payables, many=True).data,
                    "receivables": AlertaContaReceberSerializer(due_soon_receivables, many=True).data,
                },
            }
        )


# Aliases legados (urls)
FinancialDocumentViewSet = DocumentoFinanceiroViewSet
AccountPayableViewSet = ContaPagarViewSet
AccountReceivableViewSet = ContaReceberViewSet
CashFlowView = FluxoCaixaView
FinanceAlertView = AlertasFinanceirosView
