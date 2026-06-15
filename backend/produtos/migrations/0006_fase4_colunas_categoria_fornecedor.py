"""Fase 4: renomeia colunas EN restantes em produtos_categoria e produtos_fornecedor."""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("produtos", "0005_fase4_banco_pt"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            ALTER TABLE produtos_categoria RENAME COLUMN name TO nome;
            ALTER TABLE produtos_categoria RENAME COLUMN created_at TO criado_em;
            ALTER TABLE produtos_categoria RENAME COLUMN updated_at TO atualizado_em;
            ALTER TABLE produtos_fornecedor RENAME COLUMN name TO nome;
            ALTER TABLE produtos_fornecedor RENAME COLUMN legal_name TO razao_social;
            ALTER TABLE produtos_fornecedor RENAME COLUMN document TO documento;
            ALTER TABLE produtos_fornecedor RENAME COLUMN phone TO telefone;
            ALTER TABLE produtos_fornecedor RENAME COLUMN notes TO observacoes;
            ALTER TABLE produtos_fornecedor RENAME COLUMN is_active TO ativo;
            ALTER TABLE produtos_fornecedor RENAME COLUMN created_at TO criado_em;
            ALTER TABLE produtos_fornecedor RENAME COLUMN updated_at TO atualizado_em;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
