from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import generics, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from nucleo.capabilities import usuario_tem_capacidade
from nucleo.permissions import TemCapacidade
from relatorios.services import queryset_estoque_baixo

from .filters import (
    FiltroMovimentacaoEstoque,
    FiltroOrdemProducao,
    FiltroReceita,
    FiltroSaldoEstoque,
)
from .models import MovimentacaoEstoque, OrdemProducao, Receita, SaldoEstoque
from .services import cancelar_ordem_producao
from .serializers import (
    AlertaEstoqueBaixoSerializer,
    EntradaCompraWriteSerializer,
    MovimentacaoEstoqueSerializer,
    MovimentacaoEstoqueWriteSerializer,
    OrdemProducaoCreateSerializer,
    OrdemProducaoLeituraSerializer,
    ReceitaSerializer,
    SaldoEstoqueSerializer,
)


class ListaAlertaEstoqueBaixo(generics.ListAPIView):
    permission_classes = [IsAuthenticated, TemCapacidade]
    required_capability = "estoque_leitura"
    serializer_class = AlertaEstoqueBaixoSerializer
    pagination_class = None
    filter_backends = [SearchFilter]
    search_fields = ["produto__sku", "produto__nome"]

    def get_queryset(self):
        return queryset_estoque_baixo()


class SaldoEstoqueViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated, TemCapacidade]
    required_capability = "estoque_leitura"
    queryset = SaldoEstoque.objects.select_related("produto").all()
    serializer_class = SaldoEstoqueSerializer
    filterset_class = FiltroSaldoEstoque
    search_fields = ["produto__sku", "produto__nome"]
    ordering_fields = ["quantidade", "produto__nome", "id"]
    ordering = ["produto__nome"]


class MovimentacaoEstoqueViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated, TemCapacidade]
    required_capability = "estoque_movimentacoes"
    queryset = MovimentacaoEstoque.objects.select_related(
        "produto", "ordem_producao", "criado_por"
    ).all()
    filterset_class = FiltroMovimentacaoEstoque
    search_fields = ["produto__sku", "observacoes"]
    ordering_fields = ["criado_em", "id", "delta_quantidade"]
    ordering = ["-criado_em"]

    def get_serializer_class(self):
        if self.action == "create":
            return MovimentacaoEstoqueWriteSerializer
        return MovimentacaoEstoqueSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        movement = serializer.save()
        out = MovimentacaoEstoqueSerializer(movement, context={"request": request})
        return Response(out.data, status=status.HTTP_201_CREATED)


class ReceitaViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, TemCapacidade]
    required_capability = "receitas_producao"
    queryset = Receita.objects.select_related("produto").prefetch_related("linhas__insumo").all()
    serializer_class = ReceitaSerializer
    filterset_class = FiltroReceita
    search_fields = ["produto__sku", "produto__nome", "observacoes"]
    ordering_fields = ["atualizado_em", "id"]
    ordering = ["-atualizado_em"]


class OrdemProducaoViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated, TemCapacidade]
    required_capability = "receitas_producao"
    queryset = (
        OrdemProducao.objects.select_related("produto", "criado_por", "cancelada_por")
        .prefetch_related("linhas__insumo")
        .all()
    )
    filterset_class = FiltroOrdemProducao
    search_fields = ["produto__sku", "observacoes"]
    ordering_fields = ["criado_em", "id", "quantidade_produzida"]
    ordering = ["-criado_em"]

    def get_serializer_class(self):
        if self.action == "create":
            return OrdemProducaoCreateSerializer
        return OrdemProducaoLeituraSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        run = serializer.save()
        read = OrdemProducaoLeituraSerializer(run, context={"request": request})
        return Response(read.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="cancelar")
    def cancelar(self, request, pk=None):
        ordem = self.get_object()
        try:
            ordem = cancelar_ordem_producao(ordem=ordem, user=request.user)
        except DjangoValidationError as exc:
            raise DRFValidationError(detail=list(exc.messages)) from exc
        serializer = OrdemProducaoLeituraSerializer(ordem, context={"request": request})
        return Response(serializer.data)


class RegistrarEntradaCompraView(APIView):
    """
    Entrada de estoque multi-produto com geração de uma conta a pagar.
    Exige capacidades ``estoque_movimentacoes`` e ``financeiro``.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not usuario_tem_capacidade(request.user, "estoque_movimentacoes"):
            return Response(
                {"detail": "Sem permissão para movimentar estoque."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not usuario_tem_capacidade(request.user, "financeiro"):
            return Response(
                {"detail": "Sem permissão para lançamentos financeiros."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = EntradaCompraWriteSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.save()
        return Response(data, status=status.HTTP_201_CREATED)


# Aliases legados (urls)
LowStockAlertList = ListaAlertaEstoqueBaixo
StockBalanceViewSet = SaldoEstoqueViewSet
StockMovementViewSet = MovimentacaoEstoqueViewSet
RecipeViewSet = ReceitaViewSet
ProductionRunViewSet = OrdemProducaoViewSet
