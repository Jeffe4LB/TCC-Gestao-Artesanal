from django.db.models.signals import post_save
from django.dispatch import receiver

from produtos.models import Produto

from .models import SaldoEstoque


@receiver(post_save, sender=Produto)
def criar_saldo_estoque_vazio(sender, instance: Produto, created: bool, **kwargs) -> None:
    if created:
        SaldoEstoque.objects.get_or_create(produto=instance, defaults={"quantidade": 0})


# Alias legado
create_empty_stock_balance = criar_saldo_estoque_vazio
