"""Fase 3: renomeia modelos/campos de estoque no estado Django (banco inalterado)."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("financeiro", "0006_fase3_codigo_pt"),
        ("produtos", "0004_fase3_codigo_pt"),
        ("estoque", "0005_fase3_codigo_pt"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                # --- SaldoEstoque ---
                migrations.RenameModel(old_name="StockBalance", new_name="SaldoEstoque"),
                migrations.RenameField(model_name="SaldoEstoque", old_name="product", new_name="produto"),
                migrations.RenameField(model_name="SaldoEstoque", old_name="quantity", new_name="quantidade"),
                migrations.AlterModelTable(name="saldoestoque", table="estoque_stockbalance"),
                migrations.AlterField(
                    model_name="saldoestoque",
                    name="produto",
                    field=models.OneToOneField(
                        db_column="product_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="saldo_estoque",
                        to="produtos.produto",
                        verbose_name="produto",
                    ),
                ),
                migrations.AlterField(
                    model_name="saldoestoque",
                    name="quantidade",
                    field=models.DecimalField(
                        db_column="quantity",
                        decimal_places=3,
                        default=0,
                        max_digits=14,
                        verbose_name="quantidade",
                    ),
                ),
                # --- OrdemProducao (antes de MovimentacaoEstoque.ordem_producao) ---
                migrations.RenameModel(old_name="ProductionRun", new_name="OrdemProducao"),
                migrations.RenameField(model_name="OrdemProducao", old_name="product", new_name="produto"),
                migrations.RenameField(
                    model_name="OrdemProducao", old_name="quantity_produced", new_name="quantidade_produzida"
                ),
                migrations.RenameField(model_name="OrdemProducao", old_name="notes", new_name="observacoes"),
                migrations.RenameField(model_name="OrdemProducao", old_name="created_by", new_name="criado_por"),
                migrations.RenameField(model_name="OrdemProducao", old_name="created_at", new_name="criado_em"),
                migrations.AlterModelTable(name="ordemproducao", table="estoque_productionrun"),
                migrations.AlterField(
                    model_name="ordemproducao",
                    name="produto",
                    field=models.ForeignKey(
                        db_column="product_id",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="ordens_producao",
                        to="produtos.produto",
                        verbose_name="produto fabricado",
                    ),
                ),
                migrations.AlterField(
                    model_name="ordemproducao",
                    name="quantidade_produzida",
                    field=models.DecimalField(
                        db_column="quantity_produced",
                        decimal_places=3,
                        max_digits=14,
                        verbose_name="quantidade produzida",
                    ),
                ),
                migrations.AlterField(
                    model_name="ordemproducao",
                    name="observacoes",
                    field=models.TextField(blank=True, db_column="notes", verbose_name="observações"),
                ),
                migrations.AlterField(
                    model_name="ordemproducao",
                    name="criado_por",
                    field=models.ForeignKey(
                        blank=True,
                        db_column="created_by_id",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="ordens_producao",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                migrations.AlterField(
                    model_name="ordemproducao",
                    name="criado_em",
                    field=models.DateTimeField(auto_now_add=True, db_column="created_at"),
                ),
                # --- LinhaOrdemProducao ---
                migrations.RenameModel(old_name="ProductionRunLine", new_name="LinhaOrdemProducao"),
                migrations.RenameField(model_name="LinhaOrdemProducao", old_name="run", new_name="ordem"),
                migrations.RenameField(model_name="LinhaOrdemProducao", old_name="component", new_name="insumo"),
                migrations.RenameField(
                    model_name="LinhaOrdemProducao",
                    old_name="quantity_consumed",
                    new_name="quantidade_consumida",
                ),
                migrations.AlterModelTable(name="linhaordemproducao", table="estoque_productionrunline"),
                migrations.AlterField(
                    model_name="linhaordemproducao",
                    name="ordem",
                    field=models.ForeignKey(
                        db_column="run_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="linhas",
                        to="estoque.ordemproducao",
                        verbose_name="produção",
                    ),
                ),
                migrations.AlterField(
                    model_name="linhaordemproducao",
                    name="insumo",
                    field=models.ForeignKey(
                        db_column="component_id",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="linhas_ordem_producao",
                        to="produtos.produto",
                        verbose_name="insumo",
                    ),
                ),
                migrations.AlterField(
                    model_name="linhaordemproducao",
                    name="quantidade_consumida",
                    field=models.DecimalField(
                        db_column="quantity_consumed",
                        decimal_places=3,
                        max_digits=14,
                        verbose_name="quantidade consumida",
                    ),
                ),
                # --- Receita ---
                migrations.RenameModel(old_name="Recipe", new_name="Receita"),
                migrations.RenameField(model_name="Receita", old_name="product", new_name="produto"),
                migrations.RenameField(model_name="Receita", old_name="notes", new_name="observacoes"),
                migrations.RenameField(model_name="Receita", old_name="created_at", new_name="criado_em"),
                migrations.RenameField(model_name="Receita", old_name="updated_at", new_name="atualizado_em"),
                migrations.AlterModelTable(name="receita", table="estoque_recipe"),
                migrations.AlterField(
                    model_name="receita",
                    name="produto",
                    field=models.OneToOneField(
                        db_column="product_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="receita",
                        to="produtos.produto",
                        verbose_name="produto fabricado",
                    ),
                ),
                migrations.AlterField(
                    model_name="receita",
                    name="observacoes",
                    field=models.TextField(blank=True, db_column="notes", verbose_name="observações"),
                ),
                migrations.AlterField(
                    model_name="receita",
                    name="criado_em",
                    field=models.DateTimeField(auto_now_add=True, db_column="created_at"),
                ),
                migrations.AlterField(
                    model_name="receita",
                    name="atualizado_em",
                    field=models.DateTimeField(auto_now=True, db_column="updated_at"),
                ),
                # --- LinhaReceita ---
                migrations.RenameModel(old_name="RecipeLine", new_name="LinhaReceita"),
                migrations.RenameField(model_name="LinhaReceita", old_name="recipe", new_name="receita"),
                migrations.RenameField(model_name="LinhaReceita", old_name="component", new_name="insumo"),
                migrations.RenameField(
                    model_name="LinhaReceita",
                    old_name="quantity_per_unit",
                    new_name="quantidade_por_unidade",
                ),
                migrations.AlterModelTable(name="linhareceita", table="estoque_recipeline"),
                migrations.AlterField(
                    model_name="linhareceita",
                    name="receita",
                    field=models.ForeignKey(
                        db_column="recipe_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="linhas",
                        to="estoque.receita",
                        verbose_name="receita",
                    ),
                ),
                migrations.AlterField(
                    model_name="linhareceita",
                    name="insumo",
                    field=models.ForeignKey(
                        db_column="component_id",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="linhas_receita_insumo",
                        to="produtos.produto",
                        verbose_name="insumo",
                    ),
                ),
                migrations.AlterField(
                    model_name="linhareceita",
                    name="quantidade_por_unidade",
                    field=models.DecimalField(
                        db_column="quantity_per_unit",
                        decimal_places=3,
                        max_digits=14,
                        verbose_name="qtd por unidade fabricada",
                    ),
                ),
                # --- MovimentacaoEstoque ---
                migrations.RenameModel(old_name="StockMovement", new_name="MovimentacaoEstoque"),
                migrations.RenameField(model_name="MovimentacaoEstoque", old_name="product", new_name="produto"),
                migrations.RenameField(
                    model_name="MovimentacaoEstoque", old_name="quantity_delta", new_name="delta_quantidade"
                ),
                migrations.RenameField(
                    model_name="MovimentacaoEstoque", old_name="quantity_input", new_name="quantidade_informada"
                ),
                migrations.RenameField(
                    model_name="MovimentacaoEstoque", old_name="unit_input", new_name="unidade_informada"
                ),
                migrations.RenameField(
                    model_name="MovimentacaoEstoque", old_name="movement_type", new_name="tipo_movimentacao"
                ),
                migrations.RenameField(
                    model_name="MovimentacaoEstoque", old_name="production_run", new_name="ordem_producao"
                ),
                migrations.RenameField(
                    model_name="MovimentacaoEstoque", old_name="account_receivable", new_name="conta_receber"
                ),
                migrations.RenameField(
                    model_name="MovimentacaoEstoque",
                    old_name="receivable_sale_superseded",
                    new_name="venda_receber_substituta",
                ),
                migrations.RenameField(model_name="MovimentacaoEstoque", old_name="notes", new_name="observacoes"),
                migrations.RenameField(model_name="MovimentacaoEstoque", old_name="created_by", new_name="criado_por"),
                migrations.RenameField(model_name="MovimentacaoEstoque", old_name="created_at", new_name="criado_em"),
                migrations.AlterModelTable(name="movimentacaoestoque", table="estoque_stockmovement"),
                migrations.AlterModelOptions(
                    name="movimentacaoestoque",
                    options={
                        "ordering": ["-criado_em", "-id"],
                        "verbose_name": "movimentação",
                        "verbose_name_plural": "movimentações",
                    },
                ),
                migrations.AlterField(
                    model_name="movimentacaoestoque",
                    name="produto",
                    field=models.ForeignKey(
                        db_column="product_id",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="movimentacoes_estoque",
                        to="produtos.produto",
                        verbose_name="produto",
                    ),
                ),
                migrations.AlterField(
                    model_name="movimentacaoestoque",
                    name="delta_quantidade",
                    field=models.DecimalField(
                        db_column="quantity_delta",
                        decimal_places=3,
                        help_text="Sempre na unidade base da categoria do produto (KG, L ou UN).",
                        max_digits=14,
                        verbose_name="variação (unidade base)",
                    ),
                ),
                migrations.AlterField(
                    model_name="movimentacaoestoque",
                    name="quantidade_informada",
                    field=models.DecimalField(
                        blank=True,
                        db_column="quantity_input",
                        decimal_places=3,
                        help_text="Magnitude informada pelo usuário (opcional em lançamentos legados).",
                        max_digits=14,
                        null=True,
                        verbose_name="quantidade informada",
                    ),
                ),
                migrations.AlterField(
                    model_name="movimentacaoestoque",
                    name="unidade_informada",
                    field=models.CharField(
                        blank=True,
                        db_column="unit_input",
                        help_text="Unidade da quantidade informada (mesma categoria da unidade de cadastro do produto).",
                        max_length=3,
                        null=True,
                        verbose_name="unidade informada",
                    ),
                ),
                migrations.AlterField(
                    model_name="movimentacaoestoque",
                    name="tipo_movimentacao",
                    field=models.CharField(
                        choices=[
                            ("purchase_in", "Entrada (compra)"),
                            ("adjustment", "Ajuste manual"),
                            ("production_consumption", "Consumo (produção)"),
                            ("production_output", "Entrada produto acabado (produção)"),
                            ("receivable_sale", "Saída (venda / conta a receber)"),
                            ("receivable_sale_reversal", "Estorno (conta a receber)"),
                        ],
                        db_column="movement_type",
                        max_length=40,
                        verbose_name="tipo",
                    ),
                ),
                migrations.AlterField(
                    model_name="movimentacaoestoque",
                    name="ordem_producao",
                    field=models.ForeignKey(
                        blank=True,
                        db_column="production_run_id",
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="movimentacoes_estoque",
                        to="estoque.ordemproducao",
                        verbose_name="produção",
                    ),
                ),
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
                migrations.AlterField(
                    model_name="movimentacaoestoque",
                    name="venda_receber_substituta",
                    field=models.BooleanField(
                        db_column="receivable_sale_superseded",
                        default=False,
                        help_text="Marcado quando um estorno por edição ou cancelamento desfez o efeito desta saída.",
                        verbose_name="baixa de venda substituída",
                    ),
                ),
                migrations.AlterField(
                    model_name="movimentacaoestoque",
                    name="observacoes",
                    field=models.TextField(blank=True, db_column="notes", verbose_name="observações"),
                ),
                migrations.AlterField(
                    model_name="movimentacaoestoque",
                    name="criado_por",
                    field=models.ForeignKey(
                        blank=True,
                        db_column="created_by_id",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="movimentacoes_estoque_criadas",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                migrations.AlterField(
                    model_name="movimentacaoestoque",
                    name="criado_em",
                    field=models.DateTimeField(auto_now_add=True, db_column="created_at"),
                ),
            ],
        ),
    ]
