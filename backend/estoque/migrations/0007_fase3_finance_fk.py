"""Fase 3: FK conta_receber aponta para ContaReceber no estado Django."""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("financeiro", "0006_fase3_codigo_pt"),
        ("estoque", "0006_fase3_codigo_pt"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterField(
                    model_name="movimentacaoestoque",
                    name="conta_receber",
                    field=models.ForeignKey(
                        blank=True,
                        db_column="account_receivable_id",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="movimentacoes_estoque",
                        to="financeiro.contareceber",
                        verbose_name="conta a receber",
                    ),
                ),
            ],
        ),
    ]
