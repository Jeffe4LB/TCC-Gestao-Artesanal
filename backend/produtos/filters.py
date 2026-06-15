import django_filters

from nucleo.api_enums import tipo_produto_do_api

from .models import Fornecedor, Produto


class FiltroProduto(django_filters.FilterSet):
    categoria = django_filters.NumberFilter(field_name="categoria_id")
    tipo_produto = django_filters.CharFilter(method="filter_tipo_produto")
    ativo = django_filters.BooleanFilter(field_name="ativo")
    fornecedor = django_filters.NumberFilter(field_name="fornecedor_id")

    class Meta:
        model = Produto
        fields = ("categoria", "tipo_produto", "ativo", "fornecedor")

    def filter_tipo_produto(self, queryset, name, value):
        if not value:
            return queryset
        try:
            code = tipo_produto_do_api(value)
        except Exception:
            return queryset.none()
        return queryset.filter(tipo_produto=code)


class FiltroFornecedor(django_filters.FilterSet):
    ativo = django_filters.BooleanFilter(field_name="ativo")

    class Meta:
        model = Fornecedor
        fields = ("ativo",)
