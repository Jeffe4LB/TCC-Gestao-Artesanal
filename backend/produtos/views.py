from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from financeiro.historico_parceiro import historico_financeiro_fornecedor
from nucleo.permissions import TemCapacidade, TemCapacidadeFinanceiro

from .filters import FiltroFornecedor, FiltroProduto
from .models import Categoria, Fornecedor, HistoricoPreco, Produto
from .serializers import (
    CategoriaSerializer,
    FornecedorSerializer,
    HistoricoPrecoSerializer,
    ProdutoSerializer,
)


class CategoriaViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, TemCapacidade]
    required_capability = "dados_mestres"
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    search_fields = ["nome"]
    ordering_fields = ["nome", "criado_em", "id"]
    ordering = ["nome"]


class FornecedorViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, TemCapacidade]
    required_capability = "dados_mestres"
    queryset = Fornecedor.objects.all()
    serializer_class = FornecedorSerializer
    filterset_class = FiltroFornecedor
    search_fields = ["nome", "razao_social", "documento", "email", "telefone"]
    ordering_fields = ["nome", "criado_em", "id"]
    ordering = ["nome"]

    @action(
        detail=True,
        methods=["get"],
        url_path="historico-financeiro",
        permission_classes=[IsAuthenticated, TemCapacidadeFinanceiro],
    )
    def historico_financeiro(self, request, pk=None):
        return historico_financeiro_fornecedor(request, self.get_object())


class ProdutoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, TemCapacidade]
    required_capability = "dados_mestres"
    queryset = Produto.objects.select_related("categoria", "fornecedor").all()
    serializer_class = ProdutoSerializer
    filterset_class = FiltroProduto
    search_fields = ["sku", "nome", "descricao"]
    ordering_fields = [
        "nome",
        "sku",
        "estoque_minimo",
        "preco_venda",
        "custo_unitario",
        "criado_em",
        "id",
    ]
    ordering = ["nome"]

    @action(detail=True, methods=["get"], url_path="historico-precos")
    def historico_precos(self, request, pk=None):
        produto = self.get_object()
        qs = (
            HistoricoPreco.objects.filter(produto=produto)
            .select_related("alterado_por")
            .order_by("-alterado_em")[:200]
        )
        serializer = HistoricoPrecoSerializer(qs, many=True)
        return Response(serializer.data)
