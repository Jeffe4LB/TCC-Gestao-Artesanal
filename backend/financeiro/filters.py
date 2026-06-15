import django_filters

from nucleo.api_enums import (
    situacao_documento_do_api,
    situacao_pagar_do_api,
    situacao_receber_do_api,
    tipo_documento_do_api,
)

from .models import ContaPagar, ContaReceber, DocumentoFinanceiro


class FiltroContaPagar(django_filters.FilterSet):
    vencimento_de = django_filters.DateFilter(field_name="vencimento", lookup_expr="gte")
    vencimento_ate = django_filters.DateFilter(field_name="vencimento", lookup_expr="lte")
    due_from = django_filters.DateFilter(field_name="vencimento", lookup_expr="gte")
    due_to = django_filters.DateFilter(field_name="vencimento", lookup_expr="lte")
    situacao = django_filters.CharFilter(method="filter_situacao")
    fornecedor = django_filters.NumberFilter(field_name="fornecedor_id")
    documento = django_filters.NumberFilter(field_name="documento_id")
    documento_parcelado = django_filters.BooleanFilter(method="filter_documento_parcelado")

    class Meta:
        model = ContaPagar
        fields = (
            "situacao",
            "fornecedor",
            "documento",
            "documento_parcelado",
            "vencimento_de",
            "vencimento_ate",
            "due_from",
            "due_to",
        )

    def filter_documento_parcelado(self, queryset, name, value):
        if value is True:
            return queryset.filter(documento_id__isnull=False)
        if value is False:
            return queryset.filter(documento_id__isnull=True)
        return queryset

    def filter_situacao(self, queryset, name, value):
        if not value:
            return queryset
        try:
            code = situacao_pagar_do_api(value)
        except Exception:
            return queryset.none()
        return queryset.filter(situacao=code)


class FiltroContaReceber(django_filters.FilterSet):
    vencimento_de = django_filters.DateFilter(field_name="vencimento", lookup_expr="gte")
    vencimento_ate = django_filters.DateFilter(field_name="vencimento", lookup_expr="lte")
    due_from = django_filters.DateFilter(field_name="vencimento", lookup_expr="gte")
    due_to = django_filters.DateFilter(field_name="vencimento", lookup_expr="lte")
    situacao = django_filters.CharFilter(method="filter_situacao")
    cliente = django_filters.NumberFilter(field_name="cliente_id")
    documento = django_filters.NumberFilter(field_name="documento_id")
    documento_parcelado = django_filters.BooleanFilter(method="filter_documento_parcelado")

    class Meta:
        model = ContaReceber
        fields = (
            "situacao",
            "cliente",
            "documento",
            "documento_parcelado",
            "vencimento_de",
            "vencimento_ate",
            "due_from",
            "due_to",
        )

    def filter_documento_parcelado(self, queryset, name, value):
        if value is True:
            return queryset.filter(documento_id__isnull=False)
        if value is False:
            return queryset.filter(documento_id__isnull=True)
        return queryset

    def filter_situacao(self, queryset, name, value):
        if not value:
            return queryset
        try:
            code = situacao_receber_do_api(value)
        except Exception:
            return queryset.none()
        return queryset.filter(situacao=code)


class FiltroDocumentoFinanceiro(django_filters.FilterSet):
    tipo = django_filters.CharFilter(method="filter_tipo")
    situacao = django_filters.CharFilter(method="filter_situacao")
    fornecedor = django_filters.NumberFilter(field_name="fornecedor_id")
    cliente = django_filters.NumberFilter(field_name="cliente_id")

    class Meta:
        model = DocumentoFinanceiro
        fields = ("tipo", "situacao", "fornecedor", "cliente")

    def filter_tipo(self, queryset, name, value):
        if not value:
            return queryset
        try:
            code = tipo_documento_do_api(value)
        except Exception:
            return queryset.none()
        return queryset.filter(tipo=code)

    def filter_situacao(self, queryset, name, value):
        if not value:
            return queryset
        try:
            code = situacao_documento_do_api(value)
        except Exception:
            return queryset.none()
        return queryset.filter(situacao=code)


AccountPayableFilter = FiltroContaPagar
AccountReceivableFilter = FiltroContaReceber
FinancialDocumentFilter = FiltroDocumentoFinanceiro
