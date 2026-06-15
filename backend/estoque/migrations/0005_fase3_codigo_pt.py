"""Fase 3: FKs de estoque apontam para Produto no estado Django."""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("produtos", "0004_fase3_codigo_pt"),
        ("estoque", "0004_receivable_stock_movements"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterField(
                    model_name="stockbalance",
                    name="product",
                    field=models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="stock_balance",
                        to="produtos.produto",
                        verbose_name="produto",
                    ),
                ),
                migrations.AlterField(
                    model_name="stockmovement",
                    name="product",
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="stock_movements",
                        to="produtos.produto",
                        verbose_name="produto",
                    ),
                ),
                migrations.AlterField(
                    model_name="recipe",
                    name="product",
                    field=models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="recipe",
                        to="produtos.produto",
                        verbose_name="produto fabricado",
                    ),
                ),
                migrations.AlterField(
                    model_name="recipeline",
                    name="component",
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="recipe_lines_as_component",
                        to="produtos.produto",
                        verbose_name="insumo",
                    ),
                ),
                migrations.AlterField(
                    model_name="productionrun",
                    name="product",
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="production_runs",
                        to="produtos.produto",
                        verbose_name="produto fabricado",
                    ),
                ),
                migrations.AlterField(
                    model_name="productionrunline",
                    name="component",
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="production_run_lines",
                        to="produtos.produto",
                        verbose_name="insumo",
                    ),
                ),
            ],
        ),
    ]
