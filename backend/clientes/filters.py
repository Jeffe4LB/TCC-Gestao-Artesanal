import django_filters

from .models import Cliente


class ClienteFilter(django_filters.FilterSet):
    ativo = django_filters.BooleanFilter(field_name="ativo")

    class Meta:
        model = Cliente
        fields = ("ativo",)
