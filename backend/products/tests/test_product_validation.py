from decimal import Decimal

from django.test import TestCase

from products.models import Category, Product, Supplier
from products.serializers import ProductSerializer


class ProductSerializerValidationTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="Cat")
        self.sup = Supplier.objects.create(name="S")

    def test_purchased_rejects_zero_sale_price(self):
        ser = ProductSerializer(
            data={
                "sku": "P-ZS",
                "name": "P",
                "category": self.cat.pk,
                "product_type": "purchased",
                "unit": "UN",
                "sale_price": "0",
                "purchase_unit_cost": "5.00",
                "min_stock": "0",
                "is_active": True,
            }
        )
        self.assertFalse(ser.is_valid())
        self.assertIn("sale_price", ser.errors)

    def test_purchased_rejects_zero_purchase_cost(self):
        ser = ProductSerializer(
            data={
                "sku": "P-ZC",
                "name": "P",
                "category": self.cat.pk,
                "product_type": "purchased",
                "unit": "UN",
                "sale_price": "10.00",
                "purchase_unit_cost": "0",
                "min_stock": "0",
                "is_active": True,
            }
        )
        self.assertFalse(ser.is_valid())
        self.assertIn("purchase_unit_cost", ser.errors)

    def test_purchased_accepts_positive_values(self):
        ser = ProductSerializer(
            data={
                "sku": "P-OK",
                "name": "P",
                "category": self.cat.pk,
                "product_type": "purchased",
                "unit": "UN",
                "sale_price": "10.00",
                "purchase_unit_cost": "3.50",
                "min_stock": "0",
                "is_active": True,
            }
        )
        self.assertTrue(ser.is_valid(), ser.errors)

    def test_manufactured_accepts_zero_purchase_cost(self):
        ser = ProductSerializer(
            data={
                "sku": "M-1",
                "name": "Fab",
                "category": self.cat.pk,
                "product_type": "manufactured",
                "unit": "UN",
                "sale_price": "12.00",
                "purchase_unit_cost": "0",
                "min_stock": "0",
                "is_active": True,
            }
        )
        self.assertTrue(ser.is_valid(), ser.errors)

    def test_blank_unit_rejected(self):
        ser = ProductSerializer(
            data={
                "sku": "U-X",
                "name": "P",
                "category": self.cat.pk,
                "product_type": "purchased",
                "unit": "   ",
                "sale_price": "1.00",
                "purchase_unit_cost": "1.00",
                "min_stock": "0",
                "is_active": True,
            }
        )
        self.assertFalse(ser.is_valid())
        self.assertIn("unit", ser.errors)

    def test_update_purchased_requires_positive_cost_in_payload(self):
        p = Product.objects.create(
            sku="PATCH-1",
            name="X",
            category=self.cat,
            supplier=self.sup,
            product_type=Product.ProductType.PURCHASED,
            unit="UN",
            sale_price=Decimal("5.00"),
            purchase_unit_cost=Decimal("2.00"),
        )
        ser = ProductSerializer(
            instance=p,
            data={"purchase_unit_cost": "0.00"},
            partial=True,
        )
        self.assertFalse(ser.is_valid())
        self.assertIn("purchase_unit_cost", ser.errors)
