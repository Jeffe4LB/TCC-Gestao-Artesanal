from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from core.units import (
    assert_same_unit_category,
    base_unit_for_product_unit,
    convert_quantity,
    normalize_unit_code,
    quantity_to_base,
    signed_quantity_to_base,
)

from products.costs import finalize_product_unit_cost
from products.models import Product

from .models import (
    ProductionRun,
    ProductionRunLine,
    Recipe,
    RecipeLine,
    StockBalance,
    StockMovement,
)
from .services import apply_movement, execute_production


def _recipe_line_quantity_to_catalog(*, component: Product, quantity: Decimal, unit_raw: str) -> Decimal:
    """Converte qtd da linha da receita para a unidade de cadastro do insumo (como gravado no modelo)."""
    s = (unit_raw or "").strip()
    if not s:
        return quantity
    u = normalize_unit_code(s)
    assert_same_unit_category(u, component.unit)
    return convert_quantity(quantity, u, component.unit)


class StockBalanceSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    base_unit = serializers.SerializerMethodField(read_only=True)

    def get_base_unit(self, obj: StockBalance) -> str:
        return base_unit_for_product_unit(obj.product.unit)

    class Meta:
        model = StockBalance
        fields = ("id", "product", "product_sku", "product_name", "quantity", "base_unit")


class LowStockAlertSerializer(serializers.ModelSerializer):
    """Saldo na base ≤ mínimo convertido para a base (min_stock na unidade de cadastro do produto)."""

    product_id = serializers.IntegerField(source="product.id", read_only=True)
    sku = serializers.CharField(source="product.sku", read_only=True)
    name = serializers.CharField(source="product.name", read_only=True)
    min_stock = serializers.DecimalField(
        source="product.min_stock",
        max_digits=14,
        decimal_places=3,
        read_only=True,
    )
    current_quantity = serializers.DecimalField(
        source="quantity",
        max_digits=14,
        decimal_places=3,
        read_only=True,
    )
    gap = serializers.SerializerMethodField(read_only=True)

    def get_gap(self, obj: StockBalance) -> str:
        min_base = quantity_to_base(obj.product.min_stock, obj.product.unit)
        g = (min_base - obj.quantity).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
        return str(g)

    class Meta:
        model = StockBalance
        fields = (
            "product_id",
            "sku",
            "name",
            "min_stock",
            "current_quantity",
            "gap",
        )


class StockMovementSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    base_unit = serializers.SerializerMethodField(read_only=True)

    def get_base_unit(self, obj: StockMovement) -> str:
        return base_unit_for_product_unit(obj.product.unit)

    class Meta:
        model = StockMovement
        fields = (
            "id",
            "product",
            "product_sku",
            "quantity_delta",
            "quantity_input",
            "unit_input",
            "base_unit",
            "movement_type",
            "production_run",
            "notes",
            "created_by",
            "created_at",
        )
        read_only_fields = fields


class StockMovementWriteSerializer(serializers.Serializer):
    movement_type = serializers.ChoiceField(
        choices=[
            (StockMovement.MovementType.PURCHASE_IN, "Entrada (compra)"),
            (StockMovement.MovementType.ADJUSTMENT, "Ajuste manual"),
        ]
    )
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True))
    quantity = serializers.DecimalField(max_digits=14, decimal_places=3)
    unit = serializers.CharField(required=False, allow_blank=True, default="")
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        mt = attrs["movement_type"]
        q: Decimal = attrs["quantity"]
        product: Product = attrs["product"]
        unit_raw = (attrs.get("unit") or "").strip()
        if unit_raw:
            unit_in = normalize_unit_code(unit_raw)
        else:
            unit_in = base_unit_for_product_unit(product.unit)
        try:
            assert_same_unit_category(unit_in, product.unit)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"unit": list(exc.messages)}) from exc

        if mt == StockMovement.MovementType.PURCHASE_IN and q <= 0:
            raise serializers.ValidationError(
                {"quantity": "Na compra, a quantidade deve ser maior que zero."}
            )
        if mt == StockMovement.MovementType.ADJUSTMENT and q == 0:
            raise serializers.ValidationError({"quantity": "Ajuste não pode ser zero."})

        if mt == StockMovement.MovementType.PURCHASE_IN:
            delta = quantity_to_base(q, unit_in)
            q_in = q
        else:
            delta = signed_quantity_to_base(q, unit_in)
            q_in = q

        attrs["quantity_delta"] = delta
        attrs["unit_input"] = unit_in
        attrs["quantity_input"] = q_in
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        mt = validated_data["movement_type"]
        product = validated_data["product"]
        delta: Decimal = validated_data["quantity_delta"]
        notes = validated_data.get("notes") or ""
        q_in = validated_data.get("quantity_input")
        u_in = validated_data.get("unit_input")

        try:
            return apply_movement(
                product=product,
                quantity_delta=delta,
                movement_type=mt,
                user=request.user if request.user.is_authenticated else None,
                notes=notes,
                quantity_input=q_in,
                unit_input=u_in,
            )
        except DjangoValidationError as e:
            if hasattr(e, "error_dict") and e.error_dict:
                raise serializers.ValidationError(e.error_dict)
            msgs = getattr(e, "messages", None) or [str(e)]
            raise serializers.ValidationError(msgs)


class RecipeLineSerializer(serializers.ModelSerializer):
    component_sku = serializers.CharField(source="component.sku", read_only=True)

    class Meta:
        model = RecipeLine
        fields = ("id", "component", "component_sku", "quantity_per_unit")
        read_only_fields = ("id", "component_sku")

    def validate_quantity_per_unit(self, value: Decimal):
        if value <= 0:
            raise serializers.ValidationError("Deve ser maior que zero.")
        return value


class RecipeSerializer(serializers.ModelSerializer):
    lines = RecipeLineSerializer(many=True)

    class Meta:
        model = Recipe
        fields = ("id", "product", "notes", "lines", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_product(self, value: Product):
        if value.product_type != Product.ProductType.MANUFACTURED:
            raise serializers.ValidationError(
                "A receita só pode ser associada a produto fabricado manualmente."
            )
        return value

    def validate_lines(self, lines):
        if not lines:
            raise serializers.ValidationError("Informe ao menos um insumo na receita.")
        return lines

    def create(self, validated_data):
        lines_data = validated_data.pop("lines")
        raw_lines = self.initial_data.get("lines") if isinstance(self.initial_data, dict) else None
        recipe = Recipe.objects.create(**validated_data)
        for i, line in enumerate(lines_data):
            comp = line["component"]
            if comp.pk == recipe.product_id:
                raise serializers.ValidationError(
                    {"lines": "Insumo não pode ser o próprio produto fabricado."}
                )
            raw = raw_lines[i] if isinstance(raw_lines, list) and i < len(raw_lines) else {}
            unit_raw = (raw.get("quantity_per_unit_unit") or "").strip() if isinstance(raw, dict) else ""
            try:
                q_cat = _recipe_line_quantity_to_catalog(
                    component=comp, quantity=line["quantity_per_unit"], unit_raw=unit_raw
                )
            except DjangoValidationError as exc:
                raise serializers.ValidationError({"lines": list(exc.messages)}) from exc
            RecipeLine.objects.create(
                recipe=recipe,
                component=comp,
                quantity_per_unit=q_cat,
            )
        finalize_product_unit_cost(Product.objects.get(pk=recipe.product_id))
        return recipe

    def update(self, instance, validated_data):
        lines_data = validated_data.pop("lines", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if lines_data is not None:
            if not lines_data:
                raise serializers.ValidationError({"lines": "Informe ao menos um insumo."})
            raw_lines = self.initial_data.get("lines") if isinstance(self.initial_data, dict) else None
            instance.lines.all().delete()
            for i, line in enumerate(lines_data):
                comp = line["component"]
                if comp.pk == instance.product_id:
                    raise serializers.ValidationError(
                        {"lines": "Insumo não pode ser o próprio produto fabricado."}
                    )
                raw = raw_lines[i] if isinstance(raw_lines, list) and i < len(raw_lines) else {}
                unit_raw = (raw.get("quantity_per_unit_unit") or "").strip() if isinstance(raw, dict) else ""
                try:
                    q_cat = _recipe_line_quantity_to_catalog(
                        component=comp, quantity=line["quantity_per_unit"], unit_raw=unit_raw
                    )
                except DjangoValidationError as exc:
                    raise serializers.ValidationError({"lines": list(exc.messages)}) from exc
                RecipeLine.objects.create(
                    recipe=instance,
                    component=comp,
                    quantity_per_unit=q_cat,
                )
        finalize_product_unit_cost(instance.product)
        return instance


class ProductionRunLineReadSerializer(serializers.ModelSerializer):
    component_sku = serializers.CharField(source="component.sku", read_only=True)
    component_name = serializers.CharField(source="component.name", read_only=True)

    class Meta:
        model = ProductionRunLine
        fields = ("id", "component", "component_sku", "component_name", "quantity_consumed")


class ProductionRunReadSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    lines = ProductionRunLineReadSerializer(many=True, read_only=True)

    class Meta:
        model = ProductionRun
        fields = (
            "id",
            "product",
            "product_sku",
            "product_name",
            "quantity_produced",
            "notes",
            "lines",
            "created_by",
            "created_at",
        )


class ProductionLineInputSerializer(serializers.Serializer):
    component = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True))
    quantity_consumed = serializers.DecimalField(max_digits=14, decimal_places=3)
    quantity_consumed_unit = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_quantity_consumed(self, value: Decimal):
        if value <= 0:
            raise serializers.ValidationError("Deve ser maior que zero.")
        return value

    def validate(self, attrs):
        comp: Product = attrs["component"]
        raw = (attrs.get("quantity_consumed_unit") or "").strip()
        if raw:
            try:
                u = normalize_unit_code(raw)
            except DjangoValidationError as exc:
                raise serializers.ValidationError({"quantity_consumed_unit": list(exc.messages)}) from exc
            try:
                assert_same_unit_category(u, comp.unit)
            except DjangoValidationError as exc:
                raise serializers.ValidationError({"quantity_consumed_unit": list(exc.messages)}) from exc
        return attrs


class ProductionRunCreateSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(
            is_active=True,
            product_type=Product.ProductType.MANUFACTURED,
        )
    )
    quantity_produced = serializers.DecimalField(max_digits=14, decimal_places=3)
    quantity_produced_unit = serializers.CharField(required=False, allow_blank=True, default="")
    lines = ProductionLineInputSerializer(many=True)
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_quantity_produced(self, value: Decimal):
        if value <= 0:
            raise serializers.ValidationError("Deve ser maior que zero.")
        return value

    def validate(self, attrs):
        product: Product = attrs["product"]
        raw = (attrs.get("quantity_produced_unit") or "").strip()
        if raw:
            try:
                u = normalize_unit_code(raw)
            except DjangoValidationError as exc:
                raise serializers.ValidationError({"quantity_produced_unit": list(exc.messages)}) from exc
            try:
                assert_same_unit_category(u, product.unit)
            except DjangoValidationError as exc:
                raise serializers.ValidationError({"quantity_produced_unit": list(exc.messages)}) from exc
        return attrs

    def validate_lines(self, value):
        if not value:
            raise serializers.ValidationError("Informe ao menos um insumo consumido.")
        seen: set[int] = set()
        for row in value:
            pk = row["component"].pk
            if pk in seen:
                raise serializers.ValidationError(
                    "Há insumo repetido nas linhas. Una as quantidades em uma única linha."
                )
            seen.add(pk)
        return value

    def create(self, validated_data):
        request = self.context["request"]
        lines_payload = [
            {
                "component": row["component"].pk,
                "quantity_consumed": row["quantity_consumed"],
                "quantity_consumed_unit": (row.get("quantity_consumed_unit") or "").strip() or None,
            }
            for row in validated_data["lines"]
        ]
        try:
            return execute_production(
                product_id=validated_data["product"].pk,
                quantity_produced=validated_data["quantity_produced"],
                quantity_produced_unit=(validated_data.get("quantity_produced_unit") or "").strip() or None,
                lines=lines_payload,
                user=request.user if request.user.is_authenticated else None,
                notes=validated_data.get("notes") or "",
            )
        except DjangoValidationError as e:
            if hasattr(e, "error_dict") and e.error_dict:
                raise serializers.ValidationError(e.error_dict)
            msgs = getattr(e, "messages", None) or [str(e)]
            raise serializers.ValidationError(msgs)

