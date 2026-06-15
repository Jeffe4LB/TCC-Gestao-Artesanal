from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AccountPayableViewSet,
    AccountReceivableViewSet,
    CashFlowView,
    FinanceAlertView,
    FinancialDocumentViewSet,
)

router = DefaultRouter()
router.register(
    r"documentos-financeiros",
    FinancialDocumentViewSet,
    basename="documento-financeiro",
)
router.register(r"contas-pagar", AccountPayableViewSet, basename="conta-pagar")
router.register(r"contas-receber", AccountReceivableViewSet, basename="conta-receber")

urlpatterns = [
    path("fluxo-caixa/", CashFlowView.as_view(), name="fluxo-caixa"),
    path("alertas-financeiros/", FinanceAlertView.as_view(), name="alertas-financeiros"),
    path("", include(router.urls)),
]
