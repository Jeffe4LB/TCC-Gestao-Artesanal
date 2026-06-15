"""Fase 3: FK fornecedor em contas a pagar (coluna supplier_id inalterada)."""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("financeiro", "0004_fase3_codigo_pt"),
        ("produtos", "0004_fase3_codigo_pt"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.RenameField(
                    model_name="accountpayable",
                    old_name="supplier",
                    new_name="fornecedor",
                ),
                migrations.AlterField(
                    model_name="accountpayable",
                    name="fornecedor",
                    field=models.ForeignKey(
                        blank=True,
                        db_column="supplier_id",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="contas_pagar",
                        to="produtos.fornecedor",
                        verbose_name="fornecedor",
                    ),
                ),
                migrations.AlterField(
                    model_name="accountreceivableline",
                    name="product",
                    field=models.ForeignKey(
                        blank=True,
                        help_text="Obrigatório em novos lançamentos; nulo apenas em registros migrados.",
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="receivable_lines",
                        to="produtos.produto",
                        verbose_name="produto",
                    ),
                ),
            ],
        ),
    ]
