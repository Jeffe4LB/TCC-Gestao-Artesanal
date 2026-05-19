from datetime import date
from decimal import Decimal

from django.test import TestCase

from customers.models import Customer
from finance.serializers import AccountPayableSerializer, AccountReceivableSerializer
from products.models import Category, Product, Supplier


class AccountPayableAmountValidationTests(TestCase):
    def test_amount_must_be_positive(self):
        ser = AccountPayableSerializer(
            data={
                "description": "Conta",
                "amount": "0",
                "due_date": "2026-04-20",
                "status": "open",
                "notes": "",
            }
        )
        self.assertFalse(ser.is_valid())
        self.assertIn("amount", ser.errors)


class AccountReceivableLinePriceValidationTests(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(name="C", document="", phone="", email="")
        self.cat = Category.objects.create(name="G")
        self.sup = Supplier.objects.create(name="S")
        self.product = Product.objects.create(
            sku="PR-VAL",
            name="P",
            category=self.cat,
            supplier=self.sup,
            unit="UN",
            sale_price=Decimal("10.00"),
            purchase_unit_cost=Decimal("3.00"),
        )

    def test_unit_price_zero_invalid(self):
        ser = AccountReceivableSerializer(
            data={
                "customer": self.customer.pk,
                "description": "Doc",
                "issue_date": "2026-04-01",
                "due_date": "2026-04-15",
                "status": "open",
                "notes": "",
                "lines": [
                    {
                        "product": self.product.pk,
                        "quantity": "1",
                        "unit": "UN",
                        "unit_price": "0",
                        "discount": "0",
                    },
                ],
            }
        )
        self.assertFalse(ser.is_valid())
        self.assertIn("lines", ser.errors)
