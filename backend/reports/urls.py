from django.urls import path

from .views import (
    ReportFinanceAgingView,
    ReportFinanceCashFlowView,
    ReportFinanceOpenView,
    ReportRevenueByProductView,
    ReportStockLowView,
    ReportStockMovementsView,
    ReportStockPositionView,
)

urlpatterns = [
    path("reports/stock/position/", ReportStockPositionView.as_view(), name="report-stock-position"),
    path(
        "reports/stock/movements/",
        ReportStockMovementsView.as_view(),
        name="report-stock-movements",
    ),
    path("reports/stock/low/", ReportStockLowView.as_view(), name="report-stock-low"),
    path(
        "reports/finance/open/",
        ReportFinanceOpenView.as_view(),
        name="report-finance-open",
    ),
    path(
        "reports/finance/cash-flow/",
        ReportFinanceCashFlowView.as_view(),
        name="report-finance-cash-flow",
    ),
    path(
        "reports/finance/aging/",
        ReportFinanceAgingView.as_view(),
        name="report-finance-aging",
    ),
    path(
        "reports/finance/revenue-by-product/",
        ReportRevenueByProductView.as_view(),
        name="report-finance-revenue-by-product",
    ),
]
