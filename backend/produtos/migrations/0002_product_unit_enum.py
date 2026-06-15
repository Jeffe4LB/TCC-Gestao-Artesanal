# Generated manually — Fase 1 unidades de medida

from django.core.exceptions import ValidationError
from django.db import migrations, models


def normalize_product_units(apps, schema_editor):
    from nucleo.units import normalize_unit_code

    Product = apps.get_model("produtos", "Product")
    for p in Product.objects.all():
        try:
            nu = normalize_unit_code(p.unit or "UN")
        except ValidationError:
            nu = "UN"
        if p.unit != nu:
            p.unit = nu
            p.save(update_fields=["unit"])


class Migration(migrations.Migration):

    dependencies = [
        ("produtos", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(normalize_product_units, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="product",
            name="unit",
            field=models.CharField(
                choices=[
                    ("KG", "Quilo (KG)"),
                    ("G", "Grama (G)"),
                    ("L", "Litro (L)"),
                    ("ML", "Mililitro (ML)"),
                    ("UN", "Unidade (UN)"),
                ],
                default="UN",
                help_text="Unidade de estoque/cadastro; saldo futuro será na base da categoria (KG, L ou UN).",
                max_length=3,
                verbose_name="unidade",
            ),
        ),
    ]
