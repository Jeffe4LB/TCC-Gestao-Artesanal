from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AccountPayableViewSet,
    AccountReceivableViewSet,
    CashFlowView,
    FinanceAlertView,
)

router = DefaultRouter()
router.register(r"accounts-payable", AccountPayableViewSet, basename="accounts-payable")
router.register(
    r"accounts-receivable", AccountReceivableViewSet, basename="accounts-receivable"
)

urlpatterns = [
    path("cash-flow/", CashFlowView.as_view(), name="cash-flow"),
    path("finance-alerts/", FinanceAlertView.as_view(), name="finance-alerts"),
    path("", include(router.urls)),
]
