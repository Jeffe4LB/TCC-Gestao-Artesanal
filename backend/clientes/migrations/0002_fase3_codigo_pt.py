"""Fase 3: renomeia modelo/campos no estado Django; banco permanece igual (db_column)."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clientes", "0001_initial"),
        # Rodar após finance.0001, que ainda referencia Customer no estado.
        ("financeiro", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.RenameModel(old_name="Customer", new_name="Cliente"),
                migrations.RenameField(model_name="Cliente", old_name="name", new_name="nome"),
                migrations.RenameField(
                    model_name="Cliente", old_name="document", new_name="documento"
                ),
                migrations.RenameField(
                    model_name="Cliente", old_name="phone", new_name="telefone"
                ),
                migrations.RenameField(
                    model_name="Cliente", old_name="address", new_name="endereco"
                ),
                migrations.RenameField(
                    model_name="Cliente", old_name="is_active", new_name="ativo"
                ),
                migrations.RenameField(
                    model_name="Cliente", old_name="created_at", new_name="criado_em"
                ),
                migrations.RenameField(
                    model_name="Cliente", old_name="updated_at", new_name="atualizado_em"
                ),
                migrations.AlterModelTable(name="cliente", table="clientes_customer"),
                migrations.AlterModelOptions(
                    name="cliente",
                    options={
                        "ordering": ["nome"],
                        "verbose_name": "cliente",
                        "verbose_name_plural": "clientes",
                    },
                ),
                migrations.AlterField(
                    model_name="cliente",
                    name="nome",
                    field=models.CharField(
                        db_column="name", max_length=200, verbose_name="nome"
                    ),
                ),
                migrations.AlterField(
                    model_name="cliente",
                    name="documento",
                    field=models.CharField(
                        blank=True,
                        db_column="document",
                        max_length=20,
                        verbose_name="CPF/CNPJ",
                    ),
                ),
                migrations.AlterField(
                    model_name="cliente",
                    name="telefone",
                    field=models.CharField(
                        blank=True,
                        db_column="phone",
                        max_length=30,
                        verbose_name="telefone",
                    ),
                ),
                migrations.AlterField(
                    model_name="cliente",
                    name="endereco",
                    field=models.TextField(
                        blank=True, db_column="address", verbose_name="endereço"
                    ),
                ),
                migrations.AlterField(
                    model_name="cliente",
                    name="ativo",
                    field=models.BooleanField(
                        db_column="is_active", default=True, verbose_name="ativo"
                    ),
                ),
                migrations.AlterField(
                    model_name="cliente",
                    name="criado_em",
                    field=models.DateTimeField(
                        auto_now_add=True, db_column="created_at"
                    ),
                ),
                migrations.AlterField(
                    model_name="cliente",
                    name="atualizado_em",
                    field=models.DateTimeField(auto_now=True, db_column="updated_at"),
                ),
            ],
        ),
    ]
