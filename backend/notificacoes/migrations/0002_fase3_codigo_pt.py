"""Fase 3: renomeia modelos/campos de notifications no estado Django (banco inalterado)."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notificacoes", "0001_initial_user_notification"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.RenameModel(old_name="UserNotification", new_name="NotificacaoUsuario"),
                migrations.RenameField(model_name="NotificacaoUsuario", old_name="user", new_name="usuario"),
                migrations.RenameField(model_name="NotificacaoUsuario", old_name="level", new_name="nivel"),
                migrations.RenameField(model_name="NotificacaoUsuario", old_name="title", new_name="titulo"),
                migrations.RenameField(model_name="NotificacaoUsuario", old_name="body", new_name="mensagem"),
                migrations.RenameField(model_name="NotificacaoUsuario", old_name="read_at", new_name="lida_em"),
                migrations.RenameField(model_name="NotificacaoUsuario", old_name="created_at", new_name="criado_em"),
                migrations.AlterModelTable(
                    name="notificacaousuario", table="notificacoes_usernotification"
                ),
                migrations.AlterModelOptions(
                    name="notificacaousuario",
                    options={
                        "ordering": ["-criado_em"],
                        "verbose_name": "notificação",
                        "verbose_name_plural": "notificações",
                    },
                ),
                migrations.AlterField(
                    model_name="notificacaousuario",
                    name="usuario",
                    field=models.ForeignKey(
                        db_column="user_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notificacoes_usuario",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                migrations.AlterField(
                    model_name="notificacaousuario",
                    name="nivel",
                    field=models.CharField(
                        choices=[
                            ("success", "Sucesso"),
                            ("error", "Erro"),
                            ("info", "Informação"),
                            ("warning", "Aviso"),
                        ],
                        db_column="level",
                        default="info",
                        max_length=16,
                        verbose_name="nível",
                    ),
                ),
                migrations.AlterField(
                    model_name="notificacaousuario",
                    name="titulo",
                    field=models.CharField(db_column="title", max_length=200, verbose_name="título"),
                ),
                migrations.AlterField(
                    model_name="notificacaousuario",
                    name="mensagem",
                    field=models.TextField(blank=True, db_column="body", verbose_name="mensagem"),
                ),
                migrations.AlterField(
                    model_name="notificacaousuario",
                    name="lida_em",
                    field=models.DateTimeField(
                        blank=True, db_column="read_at", null=True, verbose_name="lida em"
                    ),
                ),
                migrations.AlterField(
                    model_name="notificacaousuario",
                    name="criado_em",
                    field=models.DateTimeField(
                        auto_now_add=True, db_column="created_at", verbose_name="criada em"
                    ),
                ),
            ],
        ),
    ]
