"""Fase 5: atualiza app_label em django_migrations e django_content_type."""

from django.db import migrations

_APP_RENAMES = [
    ("customers", "clientes"),
    ("products", "produtos"),
    ("stock", "estoque"),
    ("finance", "financeiro"),
    ("notifications", "notificacoes"),
    ("reports", "relatorios"),
    ("core", "nucleo"),
]


def _renomear_apps(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        for antigo, novo in _APP_RENAMES:
            cursor.execute(
                "UPDATE django_migrations SET app = %s WHERE app = %s",
                [novo, antigo],
            )
            cursor.execute(
                "UPDATE django_content_type SET app_label = %s WHERE app_label = %s",
                [novo, antigo],
            )


class Migration(migrations.Migration):

    dependencies = [
        ("nucleo", "0004_fase4_banco_pt"),
        ("clientes", "0003_fase4_banco_pt"),
        ("produtos", "0006_fase4_colunas_categoria_fornecedor"),
        ("estoque", "0008_fase4_banco_pt"),
        ("financeiro", "0007_fase4_banco_pt"),
        ("notificacoes", "0003_fase4_banco_pt"),
    ]

    operations = [
        migrations.RunPython(_renomear_apps, migrations.RunPython.noop),
    ]
