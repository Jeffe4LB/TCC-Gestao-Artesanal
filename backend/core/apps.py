from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "API core"

    def ready(self) -> None:
        from . import signals  # noqa: F401
