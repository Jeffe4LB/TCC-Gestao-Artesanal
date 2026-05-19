import django_filters

from .models import Customer


class CustomerFilter(django_filters.FilterSet):
    is_active = django_filters.BooleanFilter(field_name="is_active")

    class Meta:
        model = Customer
        fields = ("is_active",)
