from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from core.units import normalize_unit_code

from stock.services import sync_account_receivable_stock

from .models import AccountPayable, AccountReceivable, AccountReceivableLine


def _money(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _compute_line_total(quantity, unit_price, discount) -> Decimal:
    return _money(Decimal(str(quantity)) * Decimal(str(unit_price)) - Decimal(str(discount)))


class AccountPayableSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(
        source="supplier.name", read_only=True, allow_null=True
    )

    class Meta:
        model = AccountPayable
        fields = (
            "id",
            "supplier",
            "supplier_name",
            "description",
            "amount",
            "due_date",
            "status",
            "paid_at",
            "notes",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "supplier_name", "created_by", "created_at", "updated_at")

    def validate_amount(self, value):
        v = _money(value)
        if v <= 0:
            raise serializers.ValidationError("Valor deve ser maior que zero.")
        return v

    def validate(self, attrs):
        status = attrs.get("status")
        if status is None and self.instance:
            status = self.instance.status
        elif status is None:
            status = AccountPayable.Status.OPEN
        if "paid_at" in attrs:
            paid_at = attrs.get("paid_at")
        else:
            paid_at = self.instance.paid_at if self.instance else None

        if status != AccountPayable.Status.PAID:
            attrs["paid_at"] = None
        elif not paid_at:
            raise serializers.ValidationError(
                {"paid_at": "Informe a data efetiva do pagamento ao marcar como pago."}
            )
        return attrs


class AccountReceivableLineSerializer(serializers.ModelSerializer):
    product_sku = serializers.SerializerMethodField()

    def get_product_sku(self, obj: AccountReceivableLine):
        return obj.product.sku if obj.product_id else None

    class Meta:
        model = AccountReceivableLine
        fields = (
            "id",
            "product",
            "product_sku",
            "quantity",
            "unit",
            "unit_price",
            "discount",
            "line_total",
        )
        read_only_fields = ("id", "product_sku", "line_total")

    def validate_unit(self, value: str) -> str:
        try:
            return normalize_unit_code(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_quantity(self, value: Decimal) -> Decimal:
        if value <= 0:
            raise serializers.ValidationError("Quantidade deve ser maior que zero.")
        return value

    def validate_unit_price(self, value: Decimal) -> Decimal:
        v = _money(value)
        if v <= 0:
            raise serializers.ValidationError("Preço unitário deve ser maior que zero.")
        return v

    def validate_discount(self, value: Decimal) -> Decimal:
        if value < 0:
            raise serializers.ValidationError("Desconto não pode ser negativo.")
        return _money(value)


def _receivable_stock_user(serializer) -> object | None:
    request = serializer.context.get("request")
    if request and request.user.is_authenticated:
        return request.user
    return None


class AccountReceivableSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(
        source="customer.name", read_only=True, allow_null=True
    )
    lines = AccountReceivableLineSerializer(many=True)
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = AccountReceivable
        fields = (
            "id",
            "customer",
            "customer_name",
            "description",
            "issue_date",
            "amount",
            "due_date",
            "status",
            "received_at",
            "notes",
            "lines",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "customer_name",
            "amount",
            "created_by",
            "created_at",
            "updated_at",
        )

    def validate_lines(self, lines):
        if not lines:
            raise serializers.ValidationError("Informe ao menos uma linha com produto e valores.")
        for i, row in enumerate(lines):
            if row.get("product") is None:
                raise serializers.ValidationError(
                    f"Linha {i + 1}: selecione o produto (lançamentos antigos sem produto devem ser reeditados)."
                )
        return lines

    def validate(self, attrs):
        status = attrs.get("status")
        if status is None and self.instance:
            status = self.instance.status
        elif status is None:
            status = AccountReceivable.Status.OPEN
        if "received_at" in attrs:
            received_at = attrs.get("received_at")
        else:
            received_at = self.instance.received_at if self.instance else None

        if status != AccountReceivable.Status.PAID:
            attrs["received_at"] = None
        elif not received_at:
            raise serializers.ValidationError(
                {"received_at": "Informe a data efetiva do recebimento ao marcar como recebido."}
            )
        return attrs

    def _sync_receivable_stock_or_raise(self, receivable: AccountReceivable) -> None:
        try:
            sync_account_receivable_stock(
                receivable=receivable,
                user=_receivable_stock_user(self),
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def _write_lines(self, receivable: AccountReceivable, lines_data: list) -> Decimal:
        total = Decimal("0")
        receivable.lines.all().delete()
        for row in lines_data:
            lt = _compute_line_total(row["quantity"], row["unit_price"], row.get("discount", 0))
            if lt < 0:
                raise serializers.ValidationError(
                    {"lines": "Total da linha não pode ser negativo (verifique desconto)."}
                )
            AccountReceivableLine.objects.create(
                receivable=receivable,
                product_id=row["product"].pk if hasattr(row["product"], "pk") else row["product"],
                quantity=row["quantity"],
                unit=row["unit"],
                unit_price=row["unit_price"],
                discount=row.get("discount", 0),
                line_total=lt,
            )
            total += lt
        return _money(total)

    @transaction.atomic
    def create(self, validated_data):
        lines_data = validated_data.pop("lines")
        ar = AccountReceivable.objects.create(amount=Decimal("0"), **validated_data)
        total = self._write_lines(ar, lines_data)
        ar.amount = total
        ar.save(update_fields=["amount", "updated_at"])
        self._sync_receivable_stock_or_raise(ar)
        return ar

    @transaction.atomic
    def update(self, instance, validated_data):
        lines_data = validated_data.pop("lines", None)
        old_status = instance.status
        status_in_payload = "status" in validated_data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if lines_data is not None:
            total = self._write_lines(instance, lines_data)
            instance.amount = total
            instance.save(update_fields=["amount", "updated_at"])
        else:
            lst = list(instance.lines.all())
            if lst:
                total = _money(sum((ln.line_total for ln in lst), Decimal("0")))
                if instance.amount != total:
                    instance.amount = total
                    instance.save(update_fields=["amount", "updated_at"])
        instance.refresh_from_db()
        new_status = instance.status
        need_stock_sync = lines_data is not None or (
            status_in_payload
            and (
                new_status == AccountReceivable.Status.CANCELLED
                or old_status == AccountReceivable.Status.CANCELLED
            )
        )
        if need_stock_sync:
            self._sync_receivable_stock_or_raise(instance)
        return instance


class PayableAlertSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(
        source="supplier.name", read_only=True, allow_null=True
    )

    class Meta:
        model = AccountPayable
        fields = ("id", "description", "amount", "due_date", "supplier_name")


class ReceivableAlertSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(
        source="customer.name", read_only=True, allow_null=True
    )

    class Meta:
        model = AccountReceivable
        fields = ("id", "description", "amount", "due_date", "customer_name")
