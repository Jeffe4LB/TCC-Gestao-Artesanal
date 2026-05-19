from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("core.urls")),
    path("api/v1/", include("products.urls")),
    path("api/v1/", include("customers.urls")),
    path("api/v1/", include("stock.urls")),
    path("api/v1/", include("finance.urls")),
    path("api/v1/", include("reports.urls")),
    path("api/v1/", include("notifications.urls")),
]
