from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from nucleo.units import (
    assert_same_unit_category,
    convert_quantity,
    normalize_unit_code,
    quantity_to_base,
    signed_quantity_to_base,
    unit_category,
)


class UnitsConversionTests(SimpleTestCase):
    def test_normalize_legacy_un(self):
        self.assertEqual(normalize_unit_code("un"), "UN")
        self.assertEqual(normalize_unit_code("  kg "), "KG")

    def test_normalize_invalid(self):
        with self.assertRaises(ValidationError):
            normalize_unit_code("xl")
        with self.assertRaises(ValidationError):
            normalize_unit_code("")

    def test_categories(self):
        self.assertEqual(unit_category("G"), "PESO")
        self.assertEqual(unit_category("ML"), "VOLUME")
        self.assertEqual(unit_category("UN"), "UNIDADE")

    def test_50g_to_kg_base(self):
        """Exemplo da documentação: 50 G → 0,05 KG na base."""
        base = quantity_to_base(Decimal("50"), "G")
        self.assertEqual(base, Decimal("0.050000"))

    def test_convert_g_to_kg(self):
        self.assertEqual(convert_quantity(Decimal("50"), "G", "KG"), Decimal("0.050000"))

    def test_convert_kg_to_g(self):
        self.assertEqual(convert_quantity(Decimal("1"), "KG", "G"), Decimal("1000.000000"))

    def test_kg_to_l_forbidden(self):
        with self.assertRaises(ValidationError) as ctx:
            convert_quantity(Decimal("1"), "KG", "L")
        self.assertIn("categorias", str(ctx.exception).lower())

    def test_signed_negative_g_to_base(self):
        """Ajuste -50 G → -0,05 KG."""
        self.assertEqual(signed_quantity_to_base(Decimal("-50"), "G"), Decimal("-0.050000"))

    def test_assert_same_category_kg_g_ok(self):
        assert_same_unit_category("G", "KG")

    def test_assert_same_category_kg_l_fails(self):
        with self.assertRaises(ValidationError):
            assert_same_unit_category("L", "KG")
