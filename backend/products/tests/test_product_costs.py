from decimal import Decimal

from django.test import TestCase

from products.costs import bom_unit_cost_sum, finalize_product_unit_cost, quant_money
from products.models import Category, Product, Supplier
from stock.models import Recipe, RecipeLine


class ManufacturedCostFromBomTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="Mat")
        self.sup = Supplier.objects.create(name="Forn")
        self.comp = Product.objects.create(
            sku="INS-1",
            name="Insumo",
            category=self.cat,
            supplier=self.sup,
            product_type=Product.ProductType.PURCHASED,
            unit="KG",
            sale_price=Decimal("1.00"),
            purchase_unit_cost=Decimal("10.00"),
            unit_cost=Decimal("0"),
        )
        finalize_product_unit_cost(self.comp)
        self.comp.refresh_from_db()
        self.assertEqual(self.comp.unit_cost, Decimal("10.00"))

        self.fab = Product.objects.create(
            sku="FAB-1",
            name="Acabado",
            category=self.cat,
            product_type=Product.ProductType.MANUFACTURED,
            unit="UN",
            sale_price=Decimal("50.00"),
            purchase_unit_cost=Decimal("0"),
            unit_cost=Decimal("0"),
        )
        self.recipe = Recipe.objects.create(product=self.fab, notes="")
        RecipeLine.objects.create(
            recipe=self.recipe,
            component=self.comp,
            quantity_per_unit=Decimal("0.05"),
        )

    def test_bom_sum(self):
        finalize_product_unit_cost(self.fab)
        self.fab.refresh_from_db()
        # 0.05 KG × R$ 10/KG = R$ 0,50
        self.assertEqual(self.fab.unit_cost, Decimal("0.50"))

    def test_bom_unit_cost_sum_helper(self):
        self.assertEqual(bom_unit_cost_sum(self.fab), Decimal("0.50"))

    def test_component_price_change_propagates(self):
        finalize_product_unit_cost(self.fab)
        self.comp.purchase_unit_cost = Decimal("20.00")
        self.comp.save(update_fields=["purchase_unit_cost"])
        finalize_product_unit_cost(self.comp)
        self.fab.refresh_from_db()
        self.assertEqual(self.fab.unit_cost, quant_money(Decimal("0.05") * Decimal("20.00")))
