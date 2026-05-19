import django_filters

from .models import ProductionRun, Recipe, StockBalance, StockMovement


class StockBalanceFilter(django_filters.FilterSet):
    class Meta:
        model = StockBalance
        fields = ("product",)


class StockMovementFilter(django_filters.FilterSet):
    class Meta:
        model = StockMovement
        fields = ("product", "movement_type", "production_run")


class ProductionRunFilter(django_filters.FilterSet):
    class Meta:
        model = ProductionRun
        fields = ("product",)


class RecipeFilter(django_filters.FilterSet):
    class Meta:
        model = Recipe
        fields = ("product",)
