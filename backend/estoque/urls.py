from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    LowStockAlertList,
    ProductionRunViewSet,
    RecipeViewSet,
    RegistrarEntradaCompraView,
    StockBalanceViewSet,
    StockMovementViewSet,
)

router = DefaultRouter()
router.register(r"saldos-estoque", StockBalanceViewSet, basename="saldo-estoque")
router.register(r"movimentacoes-estoque", StockMovementViewSet, basename="movimentacao-estoque")
router.register(r"receitas", RecipeViewSet, basename="receita")
router.register(r"ordens-producao", ProductionRunViewSet, basename="ordem-producao")

urlpatterns = [
    path("alertas-estoque/", LowStockAlertList.as_view(), name="alertas-estoque"),
    path("entradas-compra/", RegistrarEntradaCompraView.as_view(), name="entradas-compra"),
    path("", include(router.urls)),
]
