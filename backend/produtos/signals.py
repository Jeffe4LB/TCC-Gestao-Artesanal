from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import HistoricoPreco, Produto


@receiver(pre_save, sender=Produto)
def capturar_estado_anterior_produto(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        instance._estado_anterior = Produto.objects.get(pk=instance.pk)
    except Produto.DoesNotExist:
        pass


@receiver(post_save, sender=Produto)
def registrar_historico_preco(sender, instance, created, **kwargs):
    if created:
        return
    anterior = getattr(instance, "_estado_anterior", None)
    if anterior is None:
        return
    if (
        anterior.preco_venda == instance.preco_venda
        and anterior.custo_unitario == instance.custo_unitario
    ):
        return
    HistoricoPreco.objects.create(
        produto=instance,
        preco_venda_anterior=anterior.preco_venda,
        preco_venda_novo=instance.preco_venda,
        custo_anterior=anterior.custo_unitario,
        custo_novo=instance.custo_unitario,
    )
