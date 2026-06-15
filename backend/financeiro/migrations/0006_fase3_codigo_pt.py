"""Fase 3: renomeia modelos/campos financeiros no estado Django (banco inalterado)."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("clientes", "0002_fase3_codigo_pt"),
        ("financeiro", "0005_fase3_codigo_pt"),
        ("produtos", "0004_fase3_codigo_pt"),
        ("estoque", "0004_receivable_stock_movements"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                # --- ContaPagar ---
                migrations.RenameModel(old_name="AccountPayable", new_name="ContaPagar"),
                migrations.RenameField(model_name="ContaPagar", old_name="description", new_name="descricao"),
                migrations.RenameField(model_name="ContaPagar", old_name="amount", new_name="valor"),
                migrations.RenameField(model_name="ContaPagar", old_name="due_date", new_name="vencimento"),
                migrations.RenameField(model_name="ContaPagar", old_name="status", new_name="situacao"),
                migrations.RenameField(model_name="ContaPagar", old_name="paid_at", new_name="pago_em"),
                migrations.RenameField(model_name="ContaPagar", old_name="notes", new_name="observacoes"),
                migrations.RenameField(model_name="ContaPagar", old_name="created_by", new_name="criado_por"),
                migrations.RenameField(model_name="ContaPagar", old_name="created_at", new_name="criado_em"),
                migrations.RenameField(model_name="ContaPagar", old_name="updated_at", new_name="atualizado_em"),
                migrations.AlterModelTable(name="contapagar", table="financeiro_accountpayable"),
                migrations.AlterModelOptions(
                    name="contapagar",
                    options={
                        "ordering": ["vencimento", "id"],
                        "verbose_name": "conta a pagar",
                        "verbose_name_plural": "contas a pagar",
                    },
                ),
                migrations.AlterField(
                    model_name="contapagar",
                    name="descricao",
                    field=models.CharField(db_column="description", max_length=300, verbose_name="descrição"),
                ),
                migrations.AlterField(
                    model_name="contapagar",
                    name="valor",
                    field=models.DecimalField(
                        db_column="amount", decimal_places=2, max_digits=14, verbose_name="valor"
                    ),
                ),
                migrations.AlterField(
                    model_name="contapagar",
                    name="vencimento",
                    field=models.DateField(db_column="due_date", verbose_name="vencimento"),
                ),
                migrations.AlterField(
                    model_name="contapagar",
                    name="situacao",
                    field=models.CharField(
                        choices=[
                            ("open", "Em aberto"),
                            ("paid", "Pago"),
                            ("cancelled", "Cancelado"),
                        ],
                        db_column="status",
                        default="open",
                        max_length=20,
                        verbose_name="situação",
                    ),
                ),
                migrations.AlterField(
                    model_name="contapagar",
                    name="pago_em",
                    field=models.DateField(
                        blank=True, db_column="paid_at", null=True, verbose_name="pago em"
                    ),
                ),
                migrations.AlterField(
                    model_name="contapagar",
                    name="observacoes",
                    field=models.TextField(blank=True, db_column="notes", verbose_name="observações"),
                ),
                migrations.AlterField(
                    model_name="contapagar",
                    name="criado_por",
                    field=models.ForeignKey(
                        blank=True,
                        db_column="created_by_id",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="contas_pagar_criadas",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                migrations.AlterField(
                    model_name="contapagar",
                    name="criado_em",
                    field=models.DateTimeField(auto_now_add=True, db_column="created_at"),
                ),
                migrations.AlterField(
                    model_name="contapagar",
                    name="atualizado_em",
                    field=models.DateTimeField(auto_now=True, db_column="updated_at"),
                ),
                # --- ContaReceber (antes de LinhaContaReceber) ---
                migrations.RenameModel(old_name="AccountReceivable", new_name="ContaReceber"),
                migrations.RenameField(model_name="ContaReceber", old_name="description", new_name="descricao"),
                migrations.RenameField(model_name="ContaReceber", old_name="issue_date", new_name="data_emissao"),
                migrations.RenameField(model_name="ContaReceber", old_name="amount", new_name="valor"),
                migrations.RenameField(model_name="ContaReceber", old_name="due_date", new_name="vencimento"),
                migrations.RenameField(model_name="ContaReceber", old_name="status", new_name="situacao"),
                migrations.RenameField(model_name="ContaReceber", old_name="received_at", new_name="recebido_em"),
                migrations.RenameField(model_name="ContaReceber", old_name="notes", new_name="observacoes"),
                migrations.RenameField(model_name="ContaReceber", old_name="created_by", new_name="criado_por"),
                migrations.RenameField(model_name="ContaReceber", old_name="created_at", new_name="criado_em"),
                migrations.RenameField(model_name="ContaReceber", old_name="updated_at", new_name="atualizado_em"),
                migrations.AlterModelTable(name="contareceber", table="financeiro_accountreceivable"),
                migrations.AlterModelOptions(
                    name="contareceber",
                    options={
                        "ordering": ["vencimento", "id"],
                        "verbose_name": "conta a receber",
                        "verbose_name_plural": "contas a receber",
                    },
                ),
                migrations.AlterField(
                    model_name="contareceber",
                    name="descricao",
                    field=models.CharField(db_column="description", max_length=300, verbose_name="descrição"),
                ),
                migrations.AlterField(
                    model_name="contareceber",
                    name="data_emissao",
                    field=models.DateField(
                        db_column="issue_date",
                        default=django.utils.timezone.now,
                        help_text="Data do documento / pedido.",
                        verbose_name="emissão",
                    ),
                ),
                migrations.AlterField(
                    model_name="contareceber",
                    name="valor",
                    field=models.DecimalField(
                        db_column="amount",
                        decimal_places=2,
                        help_text="Soma das linhas; atualizado ao salvar.",
                        max_digits=14,
                        verbose_name="valor total",
                    ),
                ),
                migrations.AlterField(
                    model_name="contareceber",
                    name="vencimento",
                    field=models.DateField(db_column="due_date", verbose_name="vencimento"),
                ),
                migrations.AlterField(
                    model_name="contareceber",
                    name="situacao",
                    field=models.CharField(
                        choices=[
                            ("open", "Em aberto"),
                            ("paid", "Recebido"),
                            ("cancelled", "Cancelado"),
                        ],
                        db_column="status",
                        default="open",
                        max_length=20,
                        verbose_name="situação",
                    ),
                ),
                migrations.AlterField(
                    model_name="contareceber",
                    name="recebido_em",
                    field=models.DateField(
                        blank=True, db_column="received_at", null=True, verbose_name="recebido em"
                    ),
                ),
                migrations.AlterField(
                    model_name="contareceber",
                    name="observacoes",
                    field=models.TextField(blank=True, db_column="notes", verbose_name="observações"),
                ),
                migrations.AlterField(
                    model_name="contareceber",
                    name="criado_por",
                    field=models.ForeignKey(
                        blank=True,
                        db_column="created_by_id",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="contas_receber_criadas",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                migrations.AlterField(
                    model_name="contareceber",
                    name="criado_em",
                    field=models.DateTimeField(auto_now_add=True, db_column="created_at"),
                ),
                migrations.AlterField(
                    model_name="contareceber",
                    name="atualizado_em",
                    field=models.DateTimeField(auto_now=True, db_column="updated_at"),
                ),
                # --- LinhaContaReceber ---
                migrations.RenameModel(old_name="AccountReceivableLine", new_name="LinhaContaReceber"),
                migrations.RenameField(
                    model_name="LinhaContaReceber", old_name="receivable", new_name="conta_receber"
                ),
                migrations.RenameField(model_name="LinhaContaReceber", old_name="product", new_name="produto"),
                migrations.RenameField(model_name="LinhaContaReceber", old_name="quantity", new_name="quantidade"),
                migrations.RenameField(model_name="LinhaContaReceber", old_name="unit", new_name="unidade"),
                migrations.RenameField(
                    model_name="LinhaContaReceber", old_name="unit_price", new_name="preco_unitario"
                ),
                migrations.RenameField(model_name="LinhaContaReceber", old_name="discount", new_name="desconto"),
                migrations.RenameField(
                    model_name="LinhaContaReceber", old_name="line_total", new_name="total_linha"
                ),
                migrations.AlterModelTable(name="linhacontareceber", table="financeiro_accountreceivableline"),
                migrations.AlterField(
                    model_name="linhacontareceber",
                    name="conta_receber",
                    field=models.ForeignKey(
                        db_column="receivable_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="linhas",
                        to="financeiro.contareceber",
                        verbose_name="lançamento",
                    ),
                ),
                migrations.AlterField(
                    model_name="linhacontareceber",
                    name="produto",
                    field=models.ForeignKey(
                        blank=True,
                        db_column="product_id",
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="linhas_conta_receber",
                        to="produtos.produto",
                        verbose_name="produto",
                    ),
                ),
                migrations.AlterField(
                    model_name="linhacontareceber",
                    name="quantidade",
                    field=models.DecimalField(
                        db_column="quantity", decimal_places=6, max_digits=14, verbose_name="quantidade"
                    ),
                ),
                migrations.AlterField(
                    model_name="linhacontareceber",
                    name="unidade",
                    field=models.CharField(db_column="unit", max_length=3, verbose_name="unidade"),
                ),
                migrations.AlterField(
                    model_name="linhacontareceber",
                    name="preco_unitario",
                    field=models.DecimalField(
                        db_column="unit_price",
                        decimal_places=2,
                        max_digits=14,
                        verbose_name="preço unitário",
                    ),
                ),
                migrations.AlterField(
                    model_name="linhacontareceber",
                    name="desconto",
                    field=models.DecimalField(
                        db_column="discount",
                        decimal_places=2,
                        default=0,
                        max_digits=14,
                        verbose_name="desconto (R$)",
                    ),
                ),
                migrations.AlterField(
                    model_name="linhacontareceber",
                    name="total_linha",
                    field=models.DecimalField(
                        db_column="line_total",
                        decimal_places=2,
                        default=0,
                        max_digits=14,
                        verbose_name="total da linha (R$)",
                    ),
                ),
            ],
        ),
    ]
