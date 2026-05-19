import django_filters

from .models import Product, Supplier


class ProductFilter(django_filters.FilterSet):
    category = django_filters.NumberFilter(field_name="category_id")
    product_type = django_filters.CharFilter(field_name="product_type")
    is_active = django_filters.BooleanFilter(field_name="is_active")

    class Meta:
        model = Product
        fields = ("category", "product_type", "is_active", "supplier")


class SupplierFilter(django_filters.FilterSet):
    is_active = django_filters.BooleanFilter(field_name="is_active")

    class Meta:
        model = Supplier
        fields = ("is_active",)
