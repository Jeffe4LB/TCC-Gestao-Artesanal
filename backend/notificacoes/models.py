from django.conf import settings
from django.db import models


class NotificacaoUsuario(models.Model):
    class Nivel(models.TextChoices):
        SUCESSO = "success", "Sucesso"
        ERRO = "error", "Erro"
        INFO = "info", "Informação"
        AVISO = "warning", "Aviso"
        CRITICO = "critical", "Crítico"

    class Tipo(models.TextChoices):
        ESTOQUE_MINIMO = "estoque_minimo", "Estoque abaixo do mínimo"
        TITULO_VENCIDO = "titulo_vencido", "Título vencido"
        TITULO_A_VENCER = "titulo_a_vencer", "Título a vencer"
        GENERICA = "generica", "Notificação"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notificacoes_usuario",
    )
    nivel = models.CharField(
        "nível",
        max_length=16,
        choices=Nivel.choices,
        default=Nivel.INFO,
    )
    tipo = models.CharField(
        "tipo",
        max_length=64,
        choices=Tipo.choices,
        default=Tipo.GENERICA,
        db_index=True,
        help_text="Categoria da notificação para agrupamento e deduplicação.",
    )
    titulo = models.CharField("título", max_length=200)
    mensagem = models.TextField("mensagem", blank=True)
    referencia_app = models.CharField(
        "app de origem",
        max_length=32,
        blank=True,
        help_text="App que originou a notificação (ex.: estoque, financeiro).",
    )
    referencia_id = models.PositiveIntegerField(
        "id de referência",
        null=True,
        blank=True,
        help_text="ID do objeto que originou a notificação (produto, conta, etc.).",
    )
    data_referencia = models.DateField(
        "data de referência",
        null=True,
        blank=True,
        db_index=True,
        help_text="Data relevante (ex.: vencimento, dia do alerta).",
    )
    chave_dedup = models.CharField(
        "chave de deduplicação",
        max_length=160,
        unique=True,
        null=True,
        blank=True,
        help_text="Identificador único para evitar criar a mesma notificação duas vezes.",
    )
    lida_em = models.DateTimeField("lida em", null=True, blank=True)
    criado_em = models.DateTimeField("criada em", auto_now_add=True)

    class Meta:
        db_table = "notificacoes_notificacaousuario"
        ordering = ["-criado_em"]
        verbose_name = "notificação"
        verbose_name_plural = "notificações"
        indexes = [
            models.Index(fields=["usuario", "lida_em"]),
            models.Index(fields=["tipo", "data_referencia"]),
        ]

    def __str__(self) -> str:
        return f"{self.titulo} ({self.usuario_id})"


# Alias legado
UserNotification = NotificacaoUsuario
