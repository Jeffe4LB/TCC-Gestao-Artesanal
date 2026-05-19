from django.contrib import admin

from .models import Category, Product, Supplier


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "document", "phone", "email", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "legal_name", "document", "email")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "sku",
        "name",
        "category",
        "product_type",
        "unit",
        "sale_price",
        "unit_cost",
        "min_stock",
        "is_active",
    )
    list_filter = ("product_type", "is_active", "category")
    search_fields = ("sku", "name", "description")
    raw_id_fields = ("category", "supplier")
