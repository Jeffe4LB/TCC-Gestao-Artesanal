"""Signals que disparam geração proativa de notificações.

Mantido em ``notificacoes/`` (e não em ``estoque/``) para deixar a lógica
de notificação coesa em um único app. O receiver usa
``transaction.on_commit`` para diferir a consulta de saldo até depois do
commit da movimentação que disparou o evento, evitando ler valores
parcialmente persistidos.
"""

from __future__ import annotations

import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from estoque.models import MovimentacaoEstoque, SaldoEstoque

log = logging.getLogger(__name__)


@receiver(post_save, sender=MovimentacaoEstoque)
def acionar_alerta_estoque_minimo(sender, instance: MovimentacaoEstoque, created: bool, **kwargs) -> None:
    """Após cada nova movimentação, checa se o saldo cruzou o mínimo.

    - Se o saldo ficou ≤ mínimo: gera notificação para usuários elegíveis
      (deduplicada por dia).
    - Se o saldo voltou acima do mínimo: marca notificações abertas
      como lidas.
    """
    if not created:
        return

    produto_id = instance.produto_id
    if not produto_id:
        return

    def _verificar() -> None:
        try:
            from .notificacoes_proativas import (
                notificar_estoque_minimo,
                resolver_notificacoes_estoque,
            )

            saldo = SaldoEstoque.objects.filter(produto_id=produto_id).first()
            produto = instance.produto
            if not saldo:
                return
            if not produto.estoque_minimo or produto.estoque_minimo <= 0:
                return
            if saldo.quantidade <= produto.estoque_minimo:
                notificar_estoque_minimo(produto=produto, saldo_atual=saldo.quantidade)
            else:
                resolver_notificacoes_estoque(produto=produto)
        except Exception:  # noqa: BLE001
            # Nunca propagar erro do signal — não pode quebrar o
            # lançamento de movimentação por causa de notificação.
            log.exception("Falha ao processar alerta de estoque mínimo para produto %s", produto_id)

    transaction.on_commit(_verificar)
