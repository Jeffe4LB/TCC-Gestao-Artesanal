from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("nucleo.urls")),
    path("api/v1/", include("produtos.urls")),
    path("api/v1/", include("clientes.urls")),
    path("api/v1/", include("estoque.urls")),
    path("api/v1/", include("financeiro.urls")),
    path("api/v1/", include("relatorios.urls")),
    path("api/v1/", include("notificacoes.urls")),
]
