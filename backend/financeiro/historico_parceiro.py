from decimal import Decimal

from django.db.models import QuerySet, Sum
from rest_framework.request import Request
from rest_framework.response import Response

from clientes.models import Cliente
from nucleo.api_enums import situacao_pagar_para_api, situacao_receber_para_api
from nucleo.pagination import PaginacaoPortugues
from produtos.models import Fornecedor

from .models import ContaPagar, ContaReceber
from .serializers import HistoricoTituloPagarSerializer, HistoricoTituloReceberSerializer

_RESUMO_RECEBER = ("aberto", "parcial", "recebido", "cancelado")
_RESUMO_PAGAR = ("aberto", "parcial", "pago", "cancelado")


def _resumo_por_situacao(
    qs: QuerySet,
    chaves: tuple[str, ...],
    para_api,
) -> dict[str, str]:
    resumo = {chave: "0.00" for chave in chaves}
    for row in qs.values("situacao").annotate(total=Sum("valor")):
        api = para_api(row["situacao"])
        if api in resumo:
            resumo[api] = str(row["total"] or Decimal("0"))
    return resumo


def _resposta_historico(
    request: Request,
    qs: QuerySet,
    resumo: dict[str, str],
    serializer_class,
) -> Response:
    paginator = PaginacaoPortugues()
    page = paginator.paginate_queryset(qs, request)
    serializer = serializer_class(page, many=True)
    return Response(
        {
            "resumo": resumo,
            "total": paginator.page.paginator.count,
            "proximo": paginator.get_next_link(),
            "anterior": paginator.get_previous_link(),
            "resultados": serializer.data,
        }
    )


def historico_financeiro_cliente(request: Request, cliente: Cliente) -> Response:
    base = ContaReceber.objects.filter(cliente=cliente)
    resumo = _resumo_por_situacao(base, _RESUMO_RECEBER, situacao_receber_para_api)
    qs = base.order_by("-vencimento", "-id")
    return _resposta_historico(request, qs, resumo, HistoricoTituloReceberSerializer)


def historico_financeiro_fornecedor(request: Request, fornecedor: Fornecedor) -> Response:
    base = ContaPagar.objects.filter(fornecedor=fornecedor)
    resumo = _resumo_por_situacao(base, _RESUMO_PAGAR, situacao_pagar_para_api)
    qs = base.order_by("-vencimento", "-id")
    return _resposta_historico(request, qs, resumo, HistoricoTituloPagarSerializer)
