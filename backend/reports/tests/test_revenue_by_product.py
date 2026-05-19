from datetime import date
from decimal import Decimal

from django.test import TestCase

from customers.models import Customer
from finance.models import AccountReceivable, AccountReceivableLine
from products.models import Category, Product, Supplier
from reports.services import revenue_by_product_rows


class RevenueByProductServiceTests(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            name="Cliente A", document="", phone="", email=""
        )
        self.other_customer = Customer.objects.create(
            name="Cliente B", document="", phone="", email=""
        )
        self.cat_a = Category.objects.create(name="CatA")
        self.cat_b = Category.objects.create(name="CatB")
        self.sup = Supplier.objects.create(name="Forn")
        self.p1 = Product.objects.create(
            sku="P1",
            name="Produto 1",
            category=self.cat_a,
            supplier=self.sup,
            unit="UN",
            sale_price=Decimal("10.00"),
            purchase_unit_cost=Decimal("4"),
            unit_cost=Decimal("4.00"),
        )
        self.p2 = Product.objects.create(
            sku="P2",
            name="Produto 2",
            category=self.cat_b,
            supplier=self.sup,
            unit="UN",
            sale_price=Decimal("5.00"),
            purchase_unit_cost=Decimal("1"),
            unit_cost=Decimal("1.00"),
        )

    def _line(self, ar, product, qty, unit_price, discount, line_total):
        AccountReceivableLine.objects.create(
            receivable=ar,
            product=product,
            quantity=qty,
            unit="UN",
            unit_price=unit_price,
            discount=discount,
            line_total=line_total,
        )

    def test_aggregates_lines_and_margin(self):
        ar = AccountReceivable.objects.create(
            customer=self.customer,
            description="Pedido",
            issue_date=date(2026, 4, 10),
            amount=Decimal("30.00"),
            due_date=date(2026, 4, 30),
            status=AccountReceivable.Status.OPEN,
        )
        self._line(ar, self.p1, Decimal("2"), Decimal("10"), Decimal("0"), Decimal("20.00"))
        self._line(ar, self.p1, Decimal("1"), Decimal("10"), Decimal("0"), Decimal("10.00"))

        rows = revenue_by_product_rows(date(2026, 4, 1), date(2026, 4, 30))
        by_sku = {r["sku"]: r for r in rows}
        self.assertIn("P1", by_sku)
        r1 = by_sku["P1"]
        self.assertEqual(r1["quantity_total"], Decimal("3"))
        self.assertEqual(r1["sales_total"], Decimal("30.00"))
        self.assertEqual(r1["cost_total"], Decimal("12.00"))
        self.assertEqual(r1["profit"], Decimal("18.00"))
        self.assertEqual(r1["margin_percent"], Decimal("60.00"))

    def test_respects_customer_filter(self):
        ar_a = AccountReceivable.objects.create(
            customer=self.customer,
            description="A",
            issue_date=date(2026, 4, 5),
            amount=Decimal("10"),
            due_date=date(2026, 4, 20),
            status=AccountReceivable.Status.OPEN,
        )
        self._line(ar_a, self.p1, Decimal("1"), Decimal("10"), Decimal("0"), Decimal("10.00"))
        ar_b = AccountReceivable.objects.create(
            customer=self.other_customer,
            description="B",
            issue_date=date(2026, 4, 5),
            amount=Decimal("10"),
            due_date=date(2026, 4, 20),
            status=AccountReceivable.Status.OPEN,
        )
        self._line(ar_b, self.p1, Decimal("1"), Decimal("10"), Decimal("0"), Decimal("10.00"))

        rows_all = revenue_by_product_rows(date(2026, 4, 1), date(2026, 4, 30))
        self.assertEqual(len(rows_all), 1)
        self.assertEqual(rows_all[0]["sales_total"], Decimal("20.00"))

        rows_a = revenue_by_product_rows(
            date(2026, 4, 1), date(2026, 4, 30), customer_id=self.customer.pk
        )
        self.assertEqual(rows_a[0]["sales_total"], Decimal("10.00"))

    def test_excludes_cancelled_and_out_of_range(self):
        ar_ok = AccountReceivable.objects.create(
            customer=self.customer,
            description="Ok",
            issue_date=date(2026, 4, 15),
            amount=Decimal("10"),
            due_date=date(2026, 4, 30),
            status=AccountReceivable.Status.OPEN,
        )
        self._line(ar_ok, self.p1, Decimal("1"), Decimal("10"), Decimal("0"), Decimal("10.00"))
        ar_bad = AccountReceivable.objects.create(
            customer=self.customer,
            description="Cancelado",
            issue_date=date(2026, 4, 15),
            amount=Decimal("99"),
            due_date=date(2026, 4, 30),
            status=AccountReceivable.Status.CANCELLED,
        )
        self._line(ar_bad, self.p1, Decimal("9"), Decimal("10"), Decimal("0"), Decimal("90.00"))
        ar_old = AccountReceivable.objects.create(
            customer=self.customer,
            description="Fora",
            issue_date=date(2026, 1, 1),
            amount=Decimal("5"),
            due_date=date(2026, 1, 10),
            status=AccountReceivable.Status.OPEN,
        )
        self._line(ar_old, self.p1, Decimal("1"), Decimal("5"), Decimal("0"), Decimal("5.00"))

        rows = revenue_by_product_rows(date(2026, 4, 1), date(2026, 4, 30))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["sales_total"], Decimal("10.00"))

    def test_category_filter(self):
        ar = AccountReceivable.objects.create(
            customer=self.customer,
            description="Mix",
            issue_date=date(2026, 4, 2),
            amount=Decimal("15"),
            due_date=date(2026, 4, 20),
            status=AccountReceivable.Status.PAID,
            received_at=date(2026, 4, 18),
        )
        self._line(ar, self.p1, Decimal("1"), Decimal("10"), Decimal("0"), Decimal("10.00"))
        self._line(ar, self.p2, Decimal("1"), Decimal("5"), Decimal("0"), Decimal("5.00"))

        rows_a = revenue_by_product_rows(
            date(2026, 4, 1), date(2026, 4, 30), category_id=self.cat_a.pk
        )
        self.assertEqual(len(rows_a), 1)
        self.assertEqual(rows_a[0]["sku"], "P1")

        rows_b = revenue_by_product_rows(
            date(2026, 4, 1), date(2026, 4, 30), category_id=self.cat_b.pk
        )
        self.assertEqual(len(rows_b), 1)
        self.assertEqual(rows_b[0]["sku"], "P2")
