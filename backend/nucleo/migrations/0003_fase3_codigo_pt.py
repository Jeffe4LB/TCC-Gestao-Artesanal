"""Fase 3: renomeia modelos/campos de core no estado Django (banco inalterado)."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("nucleo", "0002_passwordresettoken"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                # --- TokenRedefinicaoSenha ---
                migrations.RenameModel(old_name="PasswordResetToken", new_name="TokenRedefinicaoSenha"),
                migrations.RenameField(model_name="TokenRedefinicaoSenha", old_name="user", new_name="usuario"),
                migrations.RenameField(
                    model_name="TokenRedefinicaoSenha", old_name="token_hash", new_name="hash_token"
                ),
                migrations.RenameField(
                    model_name="TokenRedefinicaoSenha", old_name="created_at", new_name="criado_em"
                ),
                migrations.RenameField(
                    model_name="TokenRedefinicaoSenha", old_name="expires_at", new_name="expira_em"
                ),
                migrations.RenameField(
                    model_name="TokenRedefinicaoSenha", old_name="used_at", new_name="usado_em"
                ),
                migrations.AlterModelTable(name="tokenredefinicaosenha", table="nucleo_passwordresettoken"),
                migrations.AlterModelOptions(
                    name="tokenredefinicaosenha",
                    options={
                        "ordering": ["-criado_em"],
                        "verbose_name": "token de redefinição de senha",
                        "verbose_name_plural": "tokens de redefinição de senha",
                    },
                ),
                migrations.AlterField(
                    model_name="tokenredefinicaosenha",
                    name="usuario",
                    field=models.ForeignKey(
                        db_column="user_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tokens_redefinicao_senha",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                migrations.AlterField(
                    model_name="tokenredefinicaosenha",
                    name="hash_token",
                    field=models.CharField(db_column="token_hash", db_index=True, max_length=64),
                ),
                migrations.AlterField(
                    model_name="tokenredefinicaosenha",
                    name="criado_em",
                    field=models.DateTimeField(auto_now_add=True, db_column="created_at"),
                ),
                migrations.AlterField(
                    model_name="tokenredefinicaosenha",
                    name="expira_em",
                    field=models.DateTimeField(db_column="expires_at"),
                ),
                migrations.AlterField(
                    model_name="tokenredefinicaosenha",
                    name="usado_em",
                    field=models.DateTimeField(blank=True, db_column="used_at", null=True),
                ),
                # --- PerfilUsuario ---
                migrations.RenameModel(old_name="UserProfile", new_name="PerfilUsuario"),
                migrations.RenameField(model_name="PerfilUsuario", old_name="user", new_name="usuario"),
                migrations.RenameField(model_name="PerfilUsuario", old_name="role", new_name="papel"),
                migrations.RenameField(
                    model_name="PerfilUsuario", old_name="collab_master_data", new_name="colaborador_dados_mestres"
                ),
                migrations.RenameField(
                    model_name="PerfilUsuario", old_name="collab_stock_read", new_name="colaborador_estoque_leitura"
                ),
                migrations.RenameField(
                    model_name="PerfilUsuario",
                    old_name="collab_stock_movements",
                    new_name="colaborador_estoque_movimentacoes",
                ),
                migrations.RenameField(
                    model_name="PerfilUsuario",
                    old_name="collab_recipes_production",
                    new_name="colaborador_receitas_producao",
                ),
                migrations.RenameField(
                    model_name="PerfilUsuario", old_name="collab_finance", new_name="colaborador_financeiro"
                ),
                migrations.RenameField(
                    model_name="PerfilUsuario", old_name="collab_reports", new_name="colaborador_relatorios"
                ),
                migrations.RenameField(
                    model_name="PerfilUsuario", old_name="collab_dashboard", new_name="colaborador_painel"
                ),
                migrations.AlterModelTable(name="perfilusuario", table="nucleo_userprofile"),
                migrations.AlterField(
                    model_name="perfilusuario",
                    name="usuario",
                    field=models.OneToOneField(
                        db_column="user_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="perfil_usuario",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                migrations.AlterField(
                    model_name="perfilusuario",
                    name="papel",
                    field=models.CharField(
                        choices=[
                            ("admin", "Administrador"),
                            ("entrepreneur", "Empreendedor"),
                            ("collaborator", "Colaborador"),
                        ],
                        db_column="role",
                        default="entrepreneur",
                        max_length=20,
                        verbose_name="papel",
                    ),
                ),
                migrations.AlterField(
                    model_name="perfilusuario",
                    name="colaborador_dados_mestres",
                    field=models.BooleanField(
                        db_column="collab_master_data",
                        default=False,
                        help_text="Cadastros: categorias, fornecedores, produtos, clientes",
                    ),
                ),
                migrations.AlterField(
                    model_name="perfilusuario",
                    name="colaborador_estoque_leitura",
                    field=models.BooleanField(
                        db_column="collab_stock_read",
                        default=True,
                        help_text="Ver saldos e alertas de estoque",
                    ),
                ),
                migrations.AlterField(
                    model_name="perfilusuario",
                    name="colaborador_estoque_movimentacoes",
                    field=models.BooleanField(
                        db_column="collab_stock_movements",
                        default=True,
                        help_text="Registrar movimentações de estoque",
                    ),
                ),
                migrations.AlterField(
                    model_name="perfilusuario",
                    name="colaborador_receitas_producao",
                    field=models.BooleanField(
                        db_column="collab_recipes_production",
                        default=False,
                        help_text="Receitas e ordens de produção",
                    ),
                ),
                migrations.AlterField(
                    model_name="perfilusuario",
                    name="colaborador_financeiro",
                    field=models.BooleanField(
                        db_column="collab_finance",
                        default=True,
                        help_text="Contas a pagar/receber, fluxo de caixa e alertas financeiros",
                    ),
                ),
                migrations.AlterField(
                    model_name="perfilusuario",
                    name="colaborador_relatorios",
                    field=models.BooleanField(
                        db_column="collab_reports",
                        default=False,
                        help_text="Relatórios consolidados",
                    ),
                ),
                migrations.AlterField(
                    model_name="perfilusuario",
                    name="colaborador_painel",
                    field=models.BooleanField(
                        db_column="collab_dashboard",
                        default=True,
                        help_text="Painel com indicadores e resumos",
                    ),
                ),
            ],
        ),
    ]
