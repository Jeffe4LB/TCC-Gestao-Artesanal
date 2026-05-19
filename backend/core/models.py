from django.conf import settings
from django.db import models


class PasswordResetToken(models.Model):
    """Token opaco de um uso para redefinição de senha (hash armazenado)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )
    token_hash = models.CharField(max_length=64, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "token de redefinição de senha"
        verbose_name_plural = "tokens de redefinição de senha"

    def __str__(self) -> str:
        return f"reset#{self.pk} user={self.user_id}"


class UserProfile(models.Model):
    """Perfil de acesso: administrador, empreendedor ou colaborador (com permissões granulares)."""

    class Role(models.TextChoices):
        ADMIN = "admin", "Administrador"
        ENTREPRENEUR = "entrepreneur", "Empreendedor"
        COLLABORATOR = "collaborator", "Colaborador"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="userprofile",
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ENTREPRENEUR,
    )
    # Permissões extras só aplicadas quando role == COLLABORATOR
    collab_master_data = models.BooleanField(
        default=False,
        help_text="Cadastros: categorias, fornecedores, produtos, clientes",
    )
    collab_stock_read = models.BooleanField(
        default=True,
        help_text="Ver saldos e alertas de estoque",
    )
    collab_stock_movements = models.BooleanField(
        default=True,
        help_text="Registrar movimentações de estoque",
    )
    collab_recipes_production = models.BooleanField(
        default=False,
        help_text="Receitas (BOM) e ordens de produção",
    )
    collab_finance = models.BooleanField(
        default=True,
        help_text="Contas a pagar/receber, fluxo de caixa e alertas financeiros",
    )
    collab_reports = models.BooleanField(
        default=False,
        help_text="Relatórios consolidados",
    )
    collab_dashboard = models.BooleanField(
        default=True,
        help_text="Painel com indicadores e resumos",
    )

    class Meta:
        verbose_name = "Perfil de usuário"
        verbose_name_plural = "Perfis de usuário"

    def __str__(self) -> str:
        return f"{self.user.username} ({self.get_role_display()})"
