"""Fase 3: FK customer → cliente (mesma coluna customer_id no banco)."""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clientes", "0002_fase3_codigo_pt"),
        ("financeiro", "0003_alter_accountreceivable_issue_date_default"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.RenameField(
                    model_name="accountreceivable",
                    old_name="customer",
                    new_name="cliente",
                ),
                migrations.AlterField(
                    model_name="accountreceivable",
                    name="cliente",
                    field=models.ForeignKey(
                        blank=True,
                        db_column="customer_id",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="contas_receber",
                        to="clientes.cliente",
                        verbose_name="cliente",
                    ),
                ),
            ],
        ),
    ]
