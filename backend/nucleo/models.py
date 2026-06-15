from django.conf import settings
from django.db import models


class TokenRedefinicaoSenha(models.Model):
    """Token opaco de um uso para redefinição de senha (hash armazenado)."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tokens_redefinicao_senha",
    )
    hash_token = models.CharField(max_length=64, db_index=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    expira_em = models.DateTimeField()
    usado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "core_tokenredefinicaosenha"
        ordering = ["-criado_em"]
        verbose_name = "token de redefinição de senha"
        verbose_name_plural = "tokens de redefinição de senha"

    def __str__(self) -> str:
        return f"reset#{self.pk} usuario={self.usuario_id}"


class PerfilUsuario(models.Model):
    """Perfil de acesso: administrador, empreendedor ou colaborador (com permissões granulares)."""

    class Papel(models.TextChoices):
        ADMIN = "admin", "Administrador"
        EMPREENDEDOR = "entrepreneur", "Empreendedor"
        COLABORADOR = "collaborator", "Colaborador"

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil_usuario",
    )
    papel = models.CharField(
        "papel",
        max_length=20,
        choices=Papel.choices,
        default=Papel.EMPREENDEDOR,
    )
    colaborador_dados_mestres = models.BooleanField(
        default=False,
        help_text="Cadastros: categorias, fornecedores, produtos, clientes",
    )
    colaborador_estoque_leitura = models.BooleanField(
        default=True,
        help_text="Ver saldos e alertas de estoque",
    )
    colaborador_estoque_movimentacoes = models.BooleanField(
        default=True,
        help_text="Registrar movimentações de estoque",
    )
    colaborador_receitas_producao = models.BooleanField(
        default=False,
        help_text="Receitas e ordens de produção",
    )
    colaborador_financeiro = models.BooleanField(
        default=True,
        help_text="Contas a pagar/receber, fluxo de caixa e alertas financeiros",
    )
    colaborador_relatorios = models.BooleanField(
        default=False,
        help_text="Relatórios consolidados",
    )
    colaborador_painel = models.BooleanField(
        default=True,
        help_text="Painel com indicadores e resumos",
    )
    senha_temporaria = models.BooleanField(
        "senha temporária",
        default=False,
        help_text="Obriga troca de senha no próximo acesso após login.",
    )

    class Meta:
        db_table = "core_perfilusuario"
        verbose_name = "perfil de usuário"
        verbose_name_plural = "perfis de usuário"

    def __str__(self) -> str:
        return f"{self.usuario.username} ({self.get_papel_display()})"


# Aliases legados
PasswordResetToken = TokenRedefinicaoSenha
UserProfile = PerfilUsuario
