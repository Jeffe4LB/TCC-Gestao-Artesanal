from django.apps import AppConfig


class NucleoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "nucleo"
    verbose_name = "Núcleo (autenticação e perfis)"

    def ready(self) -> None:
        from . import signals  # noqa: F401
