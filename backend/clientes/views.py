from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from financeiro.historico_parceiro import historico_financeiro_cliente
from nucleo.permissions import TemCapacidade, TemCapacidadeFinanceiro

from .filters import ClienteFilter
from .models import Cliente
from .serializers import ClienteSerializer


class ClienteViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, TemCapacidade]
    required_capability = "dados_mestres"
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    filterset_class = ClienteFilter
    search_fields = ["nome", "documento", "email", "telefone"]
    ordering_fields = ["nome", "criado_em", "id"]
    ordering = ["nome"]

    @action(
        detail=True,
        methods=["get"],
        url_path="historico-financeiro",
        permission_classes=[IsAuthenticated, TemCapacidadeFinanceiro],
    )
    def historico_financeiro(self, request, pk=None):
        return historico_financeiro_cliente(request, self.get_object())
