import django_filters

from .models import AccountPayable, AccountReceivable


class AccountPayableFilter(django_filters.FilterSet):
    due_from = django_filters.DateFilter(field_name="due_date", lookup_expr="gte")
    due_to = django_filters.DateFilter(field_name="due_date", lookup_expr="lte")

    class Meta:
        model = AccountPayable
        fields = ("status", "supplier", "due_from", "due_to")


class AccountReceivableFilter(django_filters.FilterSet):
    due_from = django_filters.DateFilter(field_name="due_date", lookup_expr="gte")
    due_to = django_filters.DateFilter(field_name="due_date", lookup_expr="lte")

    class Meta:
        model = AccountReceivable
        fields = ("status", "customer", "due_from", "due_to")
