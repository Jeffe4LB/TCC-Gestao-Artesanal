from django.apps import AppConfig


class ProdutosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "produtos"
    verbose_name = "Produtos e fornecedores"

    def ready(self):
        from . import signals  # noqa: F401
