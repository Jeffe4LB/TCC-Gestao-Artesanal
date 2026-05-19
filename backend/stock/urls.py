from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    LowStockAlertList,
    ProductionRunViewSet,
    RecipeViewSet,
    StockBalanceViewSet,
    StockMovementViewSet,
)

router = DefaultRouter()
router.register(r"stock-balances", StockBalanceViewSet, basename="stock-balance")
router.register(r"stock-movements", StockMovementViewSet, basename="stock-movement")
router.register(r"recipes", RecipeViewSet, basename="recipe")
router.register(r"production-runs", ProductionRunViewSet, basename="production-run")

urlpatterns = [
    path("stock-alerts/", LowStockAlertList.as_view(), name="stock-alerts"),
    path("", include(router.urls)),
]
