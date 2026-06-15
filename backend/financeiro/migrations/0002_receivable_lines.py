# Fase 4 — linhas de contas a receber

from decimal import Decimal

import django.db.models.deletion
from django.db import migrations, models
from django.utils import timezone as django_timezone


def forwards_issue_date(apps, schema_editor):
    AR = apps.get_model("financeiro", "AccountReceivable")
    for ar in AR.objects.all():
        AR.objects.filter(pk=ar.pk).update(issue_date=ar.due_date)


def forwards_seed_lines(apps, schema_editor):
    AR = apps.get_model("financeiro", "AccountReceivable")
    Line = apps.get_model("financeiro", "AccountReceivableLine")
    Product = apps.get_model("produtos", "Product")
    Category = apps.get_model("produtos", "Category")

    ph = Product.objects.filter(sku="__LEGACY_AR__").first()
    if not ph and Category.objects.exists():
        cat = Category.objects.order_by("id").first()
        ph = Product.objects.create(
            sku="__LEGACY_AR__",
            name="Item legado (ajustar)",
            category_id=cat.pk,
            supplier_id=None,
            product_type="purchased",
            unit="UN",
            sale_price=Decimal("0"),
            purchase_unit_cost=Decimal("0"),
            unit_cost=Decimal("0"),
            is_active=False,
        )

    for ar in AR.objects.all():
        if Line.objects.filter(receivable_id=ar.pk).exists():
            continue
        Line.objects.create(
            receivable_id=ar.pk,
            product_id=ph.pk if ph else None,
            quantity=Decimal("1"),
            unit="UN",
            unit_price=ar.amount,
            discount=Decimal("0"),
            line_total=ar.amount,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("financeiro", "0001_initial"),
        ("produtos", "0003_product_sale_price_and_costs"),
    ]

    operations = [
        migrations.AddField(
            model_name="accountreceivable",
            name="issue_date",
            field=models.DateField(
                blank=True,
                help_text="Data do documento / pedido.",
                null=True,
                verbose_name="emissão",
            ),
        ),
        migrations.RunPython(forwards_issue_date, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="accountreceivable",
            name="issue_date",
            field=models.DateField(
                default=django_timezone.localdate,
                help_text="Data do documento / pedido.",
                verbose_name="emissão",
            ),
        ),
        migrations.AlterField(
            model_name="accountreceivable",
            name="amount",
            field=models.DecimalField(
                decimal_places=2,
                help_text="Soma das linhas; atualizado ao salvar.",
                max_digits=14,
                verbose_name="valor total",
            ),
        ),
        migrations.CreateModel(
            name="AccountReceivableLine",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.DecimalField(decimal_places=6, max_digits=14, verbose_name="quantidade")),
                ("unit", models.CharField(max_length=3, verbose_name="unidade")),
                ("unit_price", models.DecimalField(decimal_places=2, max_digits=14, verbose_name="preço unitário")),
                ("discount", models.DecimalField(decimal_places=2, default=0, max_digits=14, verbose_name="desconto (R$)")),
                ("line_total", models.DecimalField(decimal_places=2, default=0, max_digits=14, verbose_name="total da linha (R$)")),
                ("product", models.ForeignKey(blank=True, help_text="Obrigatório em novos lançamentos; nulo apenas em registros migrados.", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="receivable_lines", to="produtos.product", verbose_name="produto")),
                ("receivable", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lines", to="financeiro.accountreceivable", verbose_name="lançamento")),
            ],
            options={
                "verbose_name": "linha a receber",
                "verbose_name_plural": "linhas a receber",
                "ordering": ["id"],
            },
        ),
        migrations.RunPython(forwards_seed_lines, migrations.RunPython.noop),
    ]
