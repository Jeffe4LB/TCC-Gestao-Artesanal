from django.apps import AppConfig


class EstoqueConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "estoque"
    verbose_name = "Estoque"

    def ready(self) -> None:
        from . import signals  # noqa: F401
