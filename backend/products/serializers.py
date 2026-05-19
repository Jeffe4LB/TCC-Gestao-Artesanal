from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from core.units import normalize_unit_code

from .costs import finalize_product_unit_cost, quant_money
from .models import Category, Product, Supplier


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = (
            "id",
            "name",
            "legal_name",
            "document",
            "phone",
            "email",
            "notes",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    supplier_name = serializers.CharField(
        source="supplier.name", read_only=True, allow_null=True
    )
    cost_origin = serializers.SerializerMethodField(read_only=True)

    def get_cost_origin(self, obj: Product) -> str:
        if obj.product_type == Product.ProductType.MANUFACTURED:
            return "bom"
        return "purchase"

    def validate_unit(self, value: str) -> str:
        if value is None or not str(value).strip():
            raise serializers.ValidationError("Selecione a unidade de cadastro.")
        try:
            return normalize_unit_code(value.strip())
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_sale_price(self, value):
        v = quant_money(value)
        if v <= 0:
            raise serializers.ValidationError("Preço de venda deve ser maior que zero.")
        return v

    def validate_purchase_unit_cost(self, value):
        return quant_money(value)

    def validate(self, attrs):
        inst = self.instance
        pt = attrs.get(
            "product_type",
            inst.product_type if inst else Product.ProductType.PURCHASED,
        )
        if pt == Product.ProductType.MANUFACTURED:
            attrs["purchase_unit_cost"] = Decimal("0")
        else:
            puc = attrs.get("purchase_unit_cost")
            if puc is None and inst is not None:
                puc = inst.purchase_unit_cost
            if puc is None:
                raise serializers.ValidationError(
                    {"purchase_unit_cost": "Informe o custo de aquisição por unidade."}
                )
            if quant_money(puc) <= 0:
                raise serializers.ValidationError(
                    {"purchase_unit_cost": "Custo de aquisição deve ser maior que zero."}
                )
        return attrs

    def create(self, validated_data):
        obj = super().create(validated_data)
        finalize_product_unit_cost(obj)
        return obj

    def update(self, instance, validated_data):
        obj = super().update(instance, validated_data)
        finalize_product_unit_cost(obj)
        return obj

    class Meta:
        model = Product
        fields = (
            "id",
            "sku",
            "name",
            "description",
            "category",
            "category_name",
            "supplier",
            "supplier_name",
            "product_type",
            "unit",
            "sale_price",
            "purchase_unit_cost",
            "unit_cost",
            "cost_origin",
            "min_stock",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "category_name",
            "supplier_name",
            "unit_cost",
            "cost_origin",
            "created_at",
            "updated_at",
        )
