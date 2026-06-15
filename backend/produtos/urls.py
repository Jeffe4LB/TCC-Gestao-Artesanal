from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CategoriaViewSet, FornecedorViewSet, ProdutoViewSet

router = DefaultRouter()
router.register(r"categorias", CategoriaViewSet, basename="categoria")
router.register(r"fornecedores", FornecedorViewSet, basename="fornecedor")
router.register(r"produtos", ProdutoViewSet, basename="produto")

urlpatterns = [
    path("", include(router.urls)),
]
