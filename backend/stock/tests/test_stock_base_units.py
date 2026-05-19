from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from core.units import quantity_to_base
from products.costs import finalize_product_unit_cost
from products.models import Category, Product, Supplier
from stock.models import StockBalance, StockMovement
from stock.services import apply_movement


class StockMovementBaseUnitTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="Mat")
        self.sup = Supplier.objects.create(name="F")
        self.p = Product.objects.create(
            sku="CERA-1",
            name="Cera",
            category=self.cat,
            supplier=self.sup,
            product_type=Product.ProductType.PURCHASED,
            unit="KG",
            sale_price=Decimal("1.00"),
            purchase_unit_cost=Decimal("1.00"),
            unit_cost=Decimal("0"),
        )
        finalize_product_unit_cost(self.p)
        self.p.refresh_from_db()
        StockBalance.objects.update_or_create(
            product=self.p,
            defaults={"quantity": Decimal("1.000")},
        )

    def test_50g_exit_reduces_kg_balance(self):
        """1 KG de saldo; saída de 50 G → restam 0,95 KG na base."""
        delta = -quantity_to_base(Decimal("50"), "G")
        apply_movement(
            product=self.p,
            quantity_delta=delta,
            movement_type=StockMovement.MovementType.ADJUSTMENT,
            quantity_input=Decimal("50"),
            unit_input="G",
        )
        b = StockBalance.objects.get(product=self.p)
        self.assertEqual(Decimal(str(b.quantity)), Decimal("0.950"))

    def test_insufficient_stock_raises(self):
        delta = -quantity_to_base(Decimal("2000"), "G")
        with self.assertRaises(ValidationError) as ctx:
            apply_movement(
                product=self.p,
                quantity_delta=delta,
                movement_type=StockMovement.MovementType.ADJUSTMENT,
            )
        self.assertIn("insuficiente", str(ctx.exception).lower())
