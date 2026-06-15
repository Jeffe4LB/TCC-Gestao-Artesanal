# Generated manually — Fase 2 produtos e custos

from decimal import Decimal

from django.db import migrations, models


def set_initial_costs(apps, schema_editor):
    Product = apps.get_model("produtos", "Product")
    Product.objects.all().update(
        sale_price=Decimal("0"),
        purchase_unit_cost=Decimal("0"),
        unit_cost=Decimal("0"),
    )


class Migration(migrations.Migration):

    dependencies = [
        ("produtos", "0002_product_unit_enum"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="sale_price",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text="Valor de venda por 1 unidade do produto (mesma unidade do campo unidade).",
                max_digits=14,
                verbose_name="preço de venda (por unidade de cadastro)",
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="purchase_unit_cost",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text="Produto comprado: custo para adquirir 1 unidade de cadastro. Fabricado: ignorado (use receita).",
                max_digits=14,
                verbose_name="custo de aquisição (por unidade)",
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="unit_cost",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text="Comprado: espelha o custo de aquisição. Fabricado: soma dos custos da BOM (recalculado).",
                max_digits=14,
                verbose_name="custo unitário atual",
            ),
        ),
        migrations.RunPython(set_initial_costs, migrations.RunPython.noop),
    ]
