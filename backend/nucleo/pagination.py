from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class PaginacaoPortugues(PageNumberPagination):
    page_size = 20
    page_size_query_param = "tamanho_pagina"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response(
            {
                "total": self.page.paginator.count,
                "proximo": self.get_next_link(),
                "anterior": self.get_previous_link(),
                "resultados": data,
            }
        )
