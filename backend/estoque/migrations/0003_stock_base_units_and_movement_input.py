# Fase 3 — saldos e deltas em unidade base; metadados de entrada na movimentação

from decimal import Decimal

from django.db import migrations, models

import nucleo.units


def forwards(apps, schema_editor):
    StockBalance = apps.get_model("estoque", "StockBalance")
    StockMovement = apps.get_model("estoque", "StockMovement")
    ProductionRun = apps.get_model("estoque", "ProductionRun")
    ProductionRunLine = apps.get_model("estoque", "ProductionRunLine")

    for run in ProductionRun.objects.select_related("product"):
        p = run.product
        try:
            new_q = nucleo.units.quantity_to_base(run.quantity_produced, p.unit)
        except Exception:
            new_q = run.quantity_produced
        ProductionRun.objects.filter(pk=run.pk).update(quantity_produced=new_q)

    for line in ProductionRunLine.objects.select_related("component"):
        c = line.component
        try:
            new_c = nucleo.units.quantity_to_base(line.quantity_consumed, c.unit)
        except Exception:
            new_c = line.quantity_consumed
        ProductionRunLine.objects.filter(pk=line.pk).update(quantity_consumed=new_c)

    for b in StockBalance.objects.select_related("product"):
        p = b.product
        try:
            new_q = nucleo.units.quantity_to_base(b.quantity, p.unit)
        except Exception:
            new_q = b.quantity
        StockBalance.objects.filter(pk=b.pk).update(quantity=new_q)

    for m in StockMovement.objects.select_related("product"):
        p = m.product
        d = Decimal(str(m.quantity_delta))
        try:
            new_d = nucleo.units.signed_quantity_to_base(d, p.unit)
            StockMovement.objects.filter(pk=m.pk).update(
                quantity_delta=new_d,
                quantity_input=abs(d),
                unit_input=p.unit,
            )
        except Exception:
            StockMovement.objects.filter(pk=m.pk).update(
                quantity_input=abs(d),
                unit_input=p.unit,
            )


class Migration(migrations.Migration):

    dependencies = [
        ("estoque", "0002_seed_stock_balances"),
    ]

    operations = [
        migrations.AddField(
            model_name="stockmovement",
            name="quantity_input",
            field=models.DecimalField(
                blank=True,
                decimal_places=3,
                help_text="Magnitude informada pelo usuário (opcional em lançamentos legados).",
                max_digits=14,
                null=True,
                verbose_name="quantidade informada",
            ),
        ),
        migrations.AddField(
            model_name="stockmovement",
            name="unit_input",
            field=models.CharField(
                blank=True,
                help_text="Unidade da quantidade informada (mesma categoria da unidade de cadastro do produto).",
                max_length=3,
                null=True,
                verbose_name="unidade informada",
            ),
        ),
        migrations.AlterField(
            model_name="stockmovement",
            name="quantity_delta",
            field=models.DecimalField(
                decimal_places=3,
                help_text="Sempre na unidade base da categoria do produto (KG, L ou UN).",
                max_digits=14,
                verbose_name="variação (unidade base)",
            ),
        ),
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
