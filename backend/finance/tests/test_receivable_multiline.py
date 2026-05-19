from datetime import date
from decimal import Decimal

from django.test import TestCase

from customers.models import Customer
from finance.models import AccountReceivable, AccountReceivableLine
from finance.serializers import AccountReceivableSerializer
from products.models import Category, Product, Supplier


class ReceivableMultilineSerializerTests(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(name="Cliente A", document="", phone="", email="")
        self.cat = Category.objects.create(name="Geral")
        self.sup = Supplier.objects.create(name="S")
        self.p1 = Product.objects.create(
            sku="P1",
            name="Produto 1",
            category=self.cat,
            supplier=self.sup,
            unit="UN",
            sale_price=Decimal("10.00"),
            purchase_unit_cost=Decimal("5"),
            unit_cost=Decimal("5"),
        )
        self.p2 = Product.objects.create(
            sku="P2",
            name="Produto 2",
            category=self.cat,
            supplier=self.sup,
            unit="KG",
            sale_price=Decimal("20.00"),
            purchase_unit_cost=Decimal("8"),
            unit_cost=Decimal("8"),
        )

    def test_create_two_lines_total_matches(self):
        ser = AccountReceivableSerializer(
            data={
                "customer": self.customer.pk,
                "description": "Pedido 1",
                "issue_date": "2026-04-01",
                "due_date": "2026-04-15",
                "status": "open",
                "notes": "",
                "lines": [
                    {
                        "product": self.p1.pk,
                        "quantity": "2",
                        "unit": "UN",
                        "unit_price": "10.00",
                        "discount": "0",
                    },
                    {
                        "product": self.p2.pk,
                        "quantity": "1",
                        "unit": "KG",
                        "unit_price": "20.00",
                        "discount": "5.00",
                    },
                ],
            }
        )
        self.assertTrue(ser.is_valid(), ser.errors)
        ar = ser.save()
        ar.refresh_from_db()
        self.assertEqual(ar.amount, Decimal("35.00"))
        self.assertEqual(ar.lines.count(), 2)
        totals = [ln.line_total for ln in ar.lines.order_by("id")]
        self.assertEqual(totals[0], Decimal("20.00"))
        self.assertEqual(totals[1], Decimal("15.00"))

    def test_update_lines_recalculates_amount(self):
        ar = AccountReceivable.objects.create(
            customer=self.customer,
            description="Doc",
            issue_date=date(2026, 4, 1),
            amount=Decimal("0"),
            due_date=date(2026, 4, 10),
            status=AccountReceivable.Status.OPEN,
        )
        AccountReceivableLine.objects.create(
            receivable=ar,
            product=self.p1,
            quantity=Decimal("1"),
            unit="UN",
            unit_price=Decimal("10"),
            discount=Decimal("0"),
            line_total=Decimal("10"),
        )
        ar.amount = Decimal("10")
        ar.save()
        ser = AccountReceivableSerializer(
            instance=ar,
            data={
                "customer": self.customer.pk,
                "description": "Doc",
                "issue_date": "2026-04-01",
                "due_date": "2026-04-10",
                "status": "open",
                "notes": "",
                "lines": [
                    {
                        "product": self.p1.pk,
                        "quantity": "3",
                        "unit": "UN",
                        "unit_price": "10.00",
                        "discount": "0",
                    },
                ],
            },
        )
        self.assertTrue(ser.is_valid(), ser.errors)
        ser.save()
        ar.refresh_from_db()
        self.assertEqual(ar.amount, Decimal("30.00"))
