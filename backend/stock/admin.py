from django.contrib import admin

from .models import (
    ProductionRun,
    ProductionRunLine,
    Recipe,
    RecipeLine,
    StockBalance,
    StockMovement,
)


@admin.register(StockBalance)
class StockBalanceAdmin(admin.ModelAdmin):
    list_display = ("product", "quantity")
    search_fields = ("product__sku", "product__name")
    raw_id_fields = ("product",)


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "quantity_delta", "movement_type", "created_at")
    list_filter = ("movement_type",)
    search_fields = ("product__sku", "notes")
    raw_id_fields = ("product", "production_run", "created_by")
    readonly_fields = ("created_at",)


class RecipeLineInline(admin.TabularInline):
    model = RecipeLine
    extra = 0
    raw_id_fields = ("component",)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("product", "updated_at")
    search_fields = ("product__sku", "product__name")
    raw_id_fields = ("product",)
    inlines = [RecipeLineInline]


@admin.register(ProductionRun)
class ProductionRunAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "quantity_produced", "created_at", "created_by")
    list_filter = ("created_at",)
    search_fields = ("product__sku", "notes")
    raw_id_fields = ("product", "created_by")
    readonly_fields = ("created_at",)


@admin.register(ProductionRunLine)
class ProductionRunLineAdmin(admin.ModelAdmin):
    list_display = ("run", "component", "quantity_consumed")
    raw_id_fields = ("run", "component")
