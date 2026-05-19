from rest_framework import generics, mixins, status, viewsets
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.permissions import HasCapability
from core.units import quantity_to_base

from .filters import (
    ProductionRunFilter,
    RecipeFilter,
    StockBalanceFilter,
    StockMovementFilter,
)
from .models import ProductionRun, Recipe, StockBalance, StockMovement
from .serializers import (
    LowStockAlertSerializer,
    ProductionRunCreateSerializer,
    ProductionRunReadSerializer,
    RecipeSerializer,
    StockBalanceSerializer,
    StockMovementSerializer,
    StockMovementWriteSerializer,
)


class LowStockAlertList(generics.ListAPIView):
    """
    Lista produtos com saldo ≤ estoque mínimo (em tempo real, sem persistência de “lido”).
    Ignora itens com min_stock = 0. Ordenação: maior gap (mais crítico) primeiro.
    """

    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = "stock_read"
    serializer_class = LowStockAlertSerializer
    filter_backends = [SearchFilter]
    search_fields = ["product__sku", "product__name"]

    def get_queryset(self):
        """
        Compara saldo (sempre na base) com estoque mínimo convertido da unidade de cadastro para a base.
        """
        qs = (
            StockBalance.objects.filter(
                product__is_active=True,
                product__min_stock__gt=0,
            )
            .select_related("product")
            .order_by("product__sku")
        )
        ids: list[int] = []
        for b in qs.iterator():
            try:
                min_base = quantity_to_base(b.product.min_stock, b.product.unit)
            except Exception:
                continue
            if b.quantity <= min_base:
                ids.append(b.pk)
        if not ids:
            return StockBalance.objects.none()
        return (
            StockBalance.objects.filter(pk__in=ids)
            .select_related("product")
            .order_by("product__sku")
        )


class StockBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = "stock_read"
    queryset = StockBalance.objects.select_related("product").all()
    serializer_class = StockBalanceSerializer
    filterset_class = StockBalanceFilter
    search_fields = ["product__sku", "product__name"]
    ordering_fields = ["quantity", "product__name", "id"]
    ordering = ["product__name"]


class StockMovementViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = "stock_movements"
    queryset = StockMovement.objects.select_related(
        "product", "production_run", "created_by"
    ).all()
    filterset_class = StockMovementFilter
    search_fields = ["product__sku", "notes"]
    ordering_fields = ["created_at", "id", "quantity_delta"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "create":
            return StockMovementWriteSerializer
        return StockMovementSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        movement = serializer.save()
        out = StockMovementSerializer(movement, context={"request": request})
        return Response(out.data, status=status.HTTP_201_CREATED)


class RecipeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = "recipes_production"
    queryset = Recipe.objects.select_related("product").prefetch_related("lines__component").all()
    serializer_class = RecipeSerializer
    filterset_class = RecipeFilter
    search_fields = ["product__sku", "product__name", "notes"]
    ordering_fields = ["updated_at", "id"]
    ordering = ["-updated_at"]


class ProductionRunViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = "recipes_production"
    queryset = (
        ProductionRun.objects.select_related("product", "created_by")
        .prefetch_related("lines__component")
        .all()
    )
    filterset_class = ProductionRunFilter
    search_fields = ["product__sku", "notes"]
    ordering_fields = ["created_at", "id", "quantity_produced"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "create":
            return ProductionRunCreateSerializer
        return ProductionRunReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        run = serializer.save()
        read = ProductionRunReadSerializer(run, context={"request": request})
        return Response(read.data, status=status.HTTP_201_CREATED)
