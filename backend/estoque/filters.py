import django_filters

from nucleo.api_enums import tipo_movimentacao_do_api

from .models import MovimentacaoEstoque, OrdemProducao, Receita, SaldoEstoque


class FiltroSaldoEstoque(django_filters.FilterSet):
    produto = django_filters.NumberFilter(field_name="produto_id")

    class Meta:
        model = SaldoEstoque
        fields = ("produto",)


class FiltroMovimentacaoEstoque(django_filters.FilterSet):
    produto = django_filters.NumberFilter(field_name="produto_id")
    tipo_movimentacao = django_filters.CharFilter(method="filter_tipo_movimentacao")
    ordem_producao = django_filters.NumberFilter(field_name="ordem_producao_id")

    class Meta:
        model = MovimentacaoEstoque
        fields = ("produto", "tipo_movimentacao", "ordem_producao")

    def filter_tipo_movimentacao(self, queryset, name, value):
        if not value:
            return queryset
        try:
            code = tipo_movimentacao_do_api(value)
        except Exception:
            return queryset.none()
        return queryset.filter(tipo_movimentacao=code)


class FiltroOrdemProducao(django_filters.FilterSet):
    produto = django_filters.NumberFilter(field_name="produto_id")
    ativa = django_filters.BooleanFilter(method="filter_ativa")

    class Meta:
        model = OrdemProducao
        fields = ("produto", "ativa")

    def filter_ativa(self, queryset, name, value):
        if value is None:
            return queryset
        if value:
            return queryset.filter(cancelada_em__isnull=True)
        return queryset.filter(cancelada_em__isnull=False)


class FiltroReceita(django_filters.FilterSet):
    produto = django_filters.NumberFilter(field_name="produto_id")

    class Meta:
        model = Receita
        fields = ("produto",)


# Aliases legados
StockBalanceFilter = FiltroSaldoEstoque
StockMovementFilter = FiltroMovimentacaoEstoque
ProductionRunFilter = FiltroOrdemProducao
RecipeFilter = FiltroReceita
