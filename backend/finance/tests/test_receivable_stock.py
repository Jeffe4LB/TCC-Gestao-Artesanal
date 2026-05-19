from decimal import Decimal

from django.db import transaction
from django.test import TestCase
from rest_framework.serializers import ValidationError as DRFValidationError

from customers.models import Customer
from finance.models import AccountReceivable
from finance.serializers import AccountReceivableSerializer
from products.models import Category, Product, Supplier
from stock.models import StockBalance, StockMovement
from stock.services import revert_active_receivable_sale_movements


class ReceivableStockIntegrationTests(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(name="Cliente", document="", phone="", email="")
        self.cat = Category.objects.create(name="Cat")
        self.sup = Supplier.objects.create(name="Forn")
        self.product = Product.objects.create(
            sku="EST-VENDA",
            name="Item",
            category=self.cat,
            supplier=self.sup,
            unit="UN",
            sale_price=Decimal("50.00"),
            purchase_unit_cost=Decimal("10.00"),
        )
        StockBalance.objects.update_or_create(
            product=self.product,
            defaults={"quantity": Decimal("100")},
        )

    def _payload(self, *, qty: str, status: str = "open"):
        return {
            "customer": self.customer.pk,
            "description": "Fatura teste",
            "issue_date": "2026-04-01",
            "due_date": "2026-04-15",
            "status": status,
            "notes": "",
            "lines": [
                {
                    "product": self.product.pk,
                    "quantity": qty,
                    "unit": "UN",
                    "unit_price": "10.00",
                    "discount": "0",
                }
            ],
        }

    def test_create_deducts_stock(self):
        ser = AccountReceivableSerializer(data=self._payload(qty="7"))
        self.assertTrue(ser.is_valid(), ser.errors)
        ar = ser.save()
        bal = StockBalance.objects.get(product=self.product)
        self.assertEqual(bal.quantity, Decimal("93"))
        self.assertEqual(
            StockMovement.objects.filter(
                account_receivable=ar,
                movement_type=StockMovement.MovementType.RECEIVABLE_SALE,
                receivable_sale_superseded=False,
            ).count(),
            1,
        )

    def test_insufficient_stock_raises(self):
        ser = AccountReceivableSerializer(data=self._payload(qty="150"))
        self.assertTrue(ser.is_valid(), ser.errors)
        with self.assertRaises(DRFValidationError):
            ser.save()

    def test_cancel_restores_stock(self):
        ser = AccountReceivableSerializer(data=self._payload(qty="6"))
        self.assertTrue(ser.is_valid(), ser.errors)
        ar = ser.save()
        self.assertEqual(StockBalance.objects.get(product=self.product).quantity, Decimal("94"))

        ser2 = AccountReceivableSerializer(instance=ar, data={"status": "cancelled"}, partial=True)
        self.assertTrue(ser2.is_valid(), ser2.errors)
        ser2.save()
        self.assertEqual(StockBalance.objects.get(product=self.product).quantity, Decimal("100"))

    def test_update_lines_rebalances_stock(self):
        ser = AccountReceivableSerializer(data=self._payload(qty="2"))
        self.assertTrue(ser.is_valid(), ser.errors)
        ar = ser.save()
        self.assertEqual(StockBalance.objects.get(product=self.product).quantity, Decimal("98"))

        ser2 = AccountReceivableSerializer(
            instance=ar,
            data=self._payload(qty="20"),
        )
        self.assertTrue(ser2.is_valid(), ser2.errors)
        ser2.save()
        self.assertEqual(StockBalance.objects.get(product=self.product).quantity, Decimal("80"))

    def test_mark_paid_does_not_double_deduct(self):
        ser = AccountReceivableSerializer(data=self._payload(qty="3"))
        self.assertTrue(ser.is_valid(), ser.errors)
        ar = ser.save()
        self.assertEqual(StockBalance.objects.get(product=self.product).quantity, Decimal("97"))

        ser2 = AccountReceivableSerializer(
            instance=ar,
            data={"status": "paid", "received_at": "2026-04-05"},
            partial=True,
        )
        self.assertTrue(ser2.is_valid(), ser2.errors)
        ser2.save()
        self.assertEqual(StockBalance.objects.get(product=self.product).quantity, Decimal("97"))

    def test_destroy_reverts_stock(self):
        ser = AccountReceivableSerializer(data=self._payload(qty="8"))
        self.assertTrue(ser.is_valid(), ser.errors)
        ar = ser.save()
        self.assertEqual(StockBalance.objects.get(product=self.product).quantity, Decimal("92"))

        with transaction.atomic():
            revert_active_receivable_sale_movements(receivable=ar, user=None)
            ar.delete()

        self.assertFalse(AccountReceivable.objects.filter(pk=ar.pk).exists())
        self.assertEqual(StockBalance.objects.get(product=self.product).quantity, Decimal("100"))
