from decimal import Decimal

from django.test import TestCase

from products.costs import finalize_product_unit_cost
from products.models import Category, Product, Supplier
from stock.serializers import RecipeSerializer


class RecipeSerializerBomCostValidationTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="Mat")
        self.sup = Supplier.objects.create(name="F")
        self.comp = Product.objects.create(
            sku="INS-R",
            name="Insumo",
            category=self.cat,
            supplier=self.sup,
            product_type=Product.ProductType.PURCHASED,
            unit="KG",
            sale_price=Decimal("1.00"),
            purchase_unit_cost=Decimal("5.00"),
        )
        finalize_product_unit_cost(self.comp)
        self.fab = Product.objects.create(
            sku="FAB-R",
            name="Acabado",
            category=self.cat,
            product_type=Product.ProductType.MANUFACTURED,
            unit="UN",
            sale_price=Decimal("20.00"),
            purchase_unit_cost=Decimal("0"),
        )

    def test_accepts_recipe_with_zero_bom_cost(self):
        """Permite salvar BOM mesmo com custo zero (cadastro em andamento)."""
        Product.objects.filter(pk=self.comp.pk).update(unit_cost=Decimal("0"))
        self.comp.refresh_from_db()
        ser = RecipeSerializer(
            data={
                "product": self.fab.pk,
                "notes": "",
                "lines": [{"component": self.comp.pk, "quantity_per_unit": "1"}],
            }
        )
        self.assertTrue(ser.is_valid(), ser.errors)
        recipe = ser.save()
        self.assertIsNotNone(recipe.pk)

    def test_accepts_positive_bom_cost(self):
        ser = RecipeSerializer(
            data={
                "product": self.fab.pk,
                "notes": "",
                "lines": [{"component": self.comp.pk, "quantity_per_unit": "0.1"}],
            }
        )
        self.assertTrue(ser.is_valid(), ser.errors)
        recipe = ser.save()
        self.assertIsNotNone(recipe.pk)
