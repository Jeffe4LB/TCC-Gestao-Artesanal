"""Fase 3: renomeia modelos/campos de produtos no estado Django (banco inalterado)."""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("produtos", "0003_product_sale_price_and_costs"),
        ("estoque", "0002_seed_stock_balances"),
        ("financeiro", "0002_receivable_lines"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.RenameModel(old_name="Category", new_name="Categoria"),
                migrations.RenameField(model_name="Categoria", old_name="name", new_name="nome"),
                migrations.RenameField(
                    model_name="Categoria", old_name="created_at", new_name="criado_em"
                ),
                migrations.RenameField(
                    model_name="Categoria", old_name="updated_at", new_name="atualizado_em"
                ),
                migrations.AlterModelTable(name="categoria", table="produtos_category"),
                migrations.RenameModel(old_name="Supplier", new_name="Fornecedor"),
                migrations.RenameField(model_name="Fornecedor", old_name="name", new_name="nome"),
                migrations.RenameField(
                    model_name="Fornecedor", old_name="legal_name", new_name="razao_social"
                ),
                migrations.RenameField(
                    model_name="Fornecedor", old_name="document", new_name="documento"
                ),
                migrations.RenameField(
                    model_name="Fornecedor", old_name="phone", new_name="telefone"
                ),
                migrations.RenameField(
                    model_name="Fornecedor", old_name="notes", new_name="observacoes"
                ),
                migrations.RenameField(
                    model_name="Fornecedor", old_name="is_active", new_name="ativo"
                ),
                migrations.RenameField(
                    model_name="Fornecedor", old_name="created_at", new_name="criado_em"
                ),
                migrations.RenameField(
                    model_name="Fornecedor", old_name="updated_at", new_name="atualizado_em"
                ),
                migrations.AlterModelTable(name="fornecedor", table="produtos_supplier"),
                migrations.RenameModel(old_name="Product", new_name="Produto"),
                migrations.RenameField(model_name="Produto", old_name="name", new_name="nome"),
                migrations.RenameField(
                    model_name="Produto", old_name="description", new_name="descricao"
                ),
                migrations.RenameField(
                    model_name="Produto", old_name="category", new_name="categoria"
                ),
                migrations.RenameField(
                    model_name="Produto", old_name="supplier", new_name="fornecedor"
                ),
                migrations.RenameField(
                    model_name="Produto", old_name="product_type", new_name="tipo_produto"
                ),
                migrations.RenameField(
                    model_name="Produto", old_name="min_stock", new_name="estoque_minimo"
                ),
                migrations.RenameField(
                    model_name="Produto", old_name="sale_price", new_name="preco_venda"
                ),
                migrations.RenameField(
                    model_name="Produto",
                    old_name="purchase_unit_cost",
                    new_name="custo_aquisicao",
                ),
                migrations.RenameField(
                    model_name="Produto", old_name="unit_cost", new_name="custo_unitario"
                ),
                migrations.RenameField(
                    model_name="Produto", old_name="is_active", new_name="ativo"
                ),
                migrations.RenameField(
                    model_name="Produto", old_name="created_at", new_name="criado_em"
                ),
                migrations.RenameField(
                    model_name="Produto", old_name="updated_at", new_name="atualizado_em"
                ),
                migrations.AlterModelTable(name="produto", table="produtos_product"),
                migrations.AlterField(
                    model_name="produto",
                    name="nome",
                    field=models.CharField(db_column="name", max_length=200, verbose_name="nome"),
                ),
                migrations.AlterField(
                    model_name="produto",
                    name="descricao",
                    field=models.TextField(blank=True, db_column="description", verbose_name="descrição"),
                ),
                migrations.AlterField(
                    model_name="produto",
                    name="categoria",
                    field=models.ForeignKey(
                        db_column="category_id",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="produtos",
                        to="produtos.categoria",
                        verbose_name="categoria",
                    ),
                ),
                migrations.AlterField(
                    model_name="produto",
                    name="fornecedor",
                    field=models.ForeignKey(
                        blank=True,
                        db_column="supplier_id",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="produtos",
                        to="produtos.fornecedor",
                        verbose_name="fornecedor",
                    ),
                ),
                migrations.AlterField(
                    model_name="produto",
                    name="tipo_produto",
                    field=models.CharField(
                        choices=[("purchased", "Comprado"), ("manufactured", "Produzido manualmente")],
                        db_column="product_type",
                        default="purchased",
                        max_length=20,
                        verbose_name="tipo",
                    ),
                ),
                migrations.AlterField(
                    model_name="produto",
                    name="estoque_minimo",
                    field=models.DecimalField(
                        db_column="min_stock",
                        decimal_places=3,
                        default=0,
                        max_digits=14,
                        verbose_name="estoque mínimo",
                    ),
                ),
                migrations.AlterField(
                    model_name="produto",
                    name="preco_venda",
                    field=models.DecimalField(
                        db_column="sale_price",
                        decimal_places=2,
                        default=0,
                        max_digits=14,
                        verbose_name="preço de venda (por unidade de cadastro)",
                    ),
                ),
                migrations.AlterField(
                    model_name="produto",
                    name="custo_aquisicao",
                    field=models.DecimalField(
                        db_column="purchase_unit_cost",
                        decimal_places=2,
                        default=0,
                        max_digits=14,
                        verbose_name="custo de aquisição (por unidade)",
                    ),
                ),
                migrations.AlterField(
                    model_name="produto",
                    name="custo_unitario",
                    field=models.DecimalField(
                        db_column="unit_cost",
                        decimal_places=2,
                        default=0,
                        max_digits=14,
                        verbose_name="custo unitário atual",
                    ),
                ),
                migrations.AlterField(
                    model_name="produto",
                    name="ativo",
                    field=models.BooleanField(db_column="is_active", default=True, verbose_name="ativo"),
                ),
                migrations.AlterField(
                    model_name="produto",
                    name="criado_em",
                    field=models.DateTimeField(auto_now_add=True, db_column="created_at"),
                ),
                migrations.AlterField(
                    model_name="produto",
                    name="atualizado_em",
                    field=models.DateTimeField(auto_now=True, db_column="updated_at"),
                ),
            ],
        ),
    ]
