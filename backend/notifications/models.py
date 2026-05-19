from django.conf import settings
from django.db import models


class UserNotification(models.Model):
    class Level(models.TextChoices):
        SUCCESS = "success", "Sucesso"
        ERROR = "error", "Erro"
        INFO = "info", "Informação"
        WARNING = "warning", "Aviso"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_notifications",
    )
    level = models.CharField(
        max_length=16,
        choices=Level.choices,
        default=Level.INFO,
    )
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.title} ({self.user_id})"
