"""Camada de geração proativa de notificações (estoque + financeiro).

Este módulo concentra:

- `criar_notificacao`: factory com **deduplicação** por chave única.
- `notificar_estoque_minimo`: dispara alerta quando saldo cai abaixo do mínimo.
- `resolver_notificacoes_estoque`: marca como lidas as alertas de estoque
  pendentes quando o saldo voltou ao normal.
- `notificar_vencimentos_pagar` / `notificar_vencimentos_receber`: gera
  alertas para títulos vencidos e a vencer (próximos 3 dias).

As funções são puras (recebem os objetos prontos) e podem ser chamadas a
partir de signals, management commands ou views.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Iterable

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.template.loader import render_to_string
from django.utils import timezone

from .models import NotificacaoUsuario

log = logging.getLogger(__name__)

User = get_user_model()


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------


DIAS_A_VENCER = 3  # janela "vencendo em breve"

CAPACIDADE_POR_TIPO = {
    NotificacaoUsuario.Tipo.ESTOQUE_MINIMO: "estoque_leitura",
    NotificacaoUsuario.Tipo.TITULO_VENCIDO: "financeiro",
    NotificacaoUsuario.Tipo.TITULO_A_VENCER: "financeiro",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _hoje() -> date:
    return timezone.localdate()


def _montar_chave_dedup(
    *,
    usuario_id: int,
    tipo: str,
    referencia_app: str,
    referencia_id: int | None,
    data_referencia: date | None,
) -> str:
    """Monta a chave única que evita criar a mesma notificação duas vezes.

    Inclui ``usuario_id`` porque cada usuário recebe sua própria notificação
    (mesmo evento, várias linhas no banco).
    """
    data_str = data_referencia.isoformat() if data_referencia else "-"
    return f"{tipo}:{referencia_app}:{referencia_id or '-'}:{data_str}:u{usuario_id}"


def usuarios_destinatarios(tipo: str) -> list:
    """Devolve os usuários que devem receber notificações deste tipo.

    Critério: usuário ativo + tem a capacidade correspondente. A checagem
    é feita pela função `usuario_tem_capacidade` do módulo `nucleo`.
    """
    # Import tardio para evitar ciclos durante o boot do Django.
    from nucleo.capabilities import usuario_tem_capacidade

    capacidade = CAPACIDADE_POR_TIPO.get(tipo)
    qs = User.objects.filter(is_active=True)
    if capacidade is None:
        return list(qs)
    return [u for u in qs if usuario_tem_capacidade(u, capacidade)]


# ---------------------------------------------------------------------------
# Núcleo: criar com deduplicação
# ---------------------------------------------------------------------------


def criar_notificacao(
    *,
    usuario,
    tipo: str,
    titulo: str,
    mensagem: str,
    nivel: str = NotificacaoUsuario.Nivel.INFO,
    referencia_app: str = "",
    referencia_id: int | None = None,
    data_referencia: date | None = None,
    enviar_email: bool = False,
    contexto_email: dict | None = None,
    template_email: str | None = None,
    assunto_email: str | None = None,
) -> NotificacaoUsuario | None:
    """Cria notificação **se ainda não existir** uma com a mesma chave.

    Devolve a instância criada (``NotificacaoUsuario``) ou ``None`` se uma
    notificação equivalente já existia (foi pulada por dedup).
    """
    if not usuario or not getattr(usuario, "pk", None):
        return None

    chave = _montar_chave_dedup(
        usuario_id=usuario.pk,
        tipo=tipo,
        referencia_app=referencia_app,
        referencia_id=referencia_id,
        data_referencia=data_referencia,
    )

    try:
        with transaction.atomic():
            obj, criado = NotificacaoUsuario.objects.get_or_create(
                chave_dedup=chave,
                defaults={
                    "usuario": usuario,
                    "tipo": tipo,
                    "titulo": titulo,
                    "mensagem": mensagem,
                    "nivel": nivel,
                    "referencia_app": referencia_app,
                    "referencia_id": referencia_id,
                    "data_referencia": data_referencia,
                },
            )
    except IntegrityError:
        # Corrida em paralelo: outra thread/transação criou antes.
        return None

    if not criado:
        return None

    if enviar_email and template_email and getattr(usuario, "email", ""):
        _enviar_email_seguro(
            destinatario=usuario.email,
            assunto=assunto_email or titulo,
            template_base=template_email,
            contexto=(contexto_email or {}) | {"notificacao": obj, "usuario": usuario},
        )

    return obj


def _enviar_email_seguro(*, destinatario: str, assunto: str, template_base: str, contexto: dict) -> None:
    """Envia e-mail HTML + texto. Falha silenciosa (apenas loga) para não
    bloquear a operação que originou a notificação.
    """
    try:
        corpo_txt = render_to_string(f"notificacoes/email/{template_base}.txt", contexto)
        corpo_html = render_to_string(f"notificacoes/email/{template_base}.html", contexto)
        send_mail(
            subject=assunto,
            message=corpo_txt,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[destinatario],
            html_message=corpo_html,
            fail_silently=True,
        )
    except Exception:  # noqa: BLE001
        log.warning("Falha ao enviar e-mail de notificação para %s", destinatario, exc_info=True)


# ---------------------------------------------------------------------------
# Estoque mínimo
# ---------------------------------------------------------------------------


def notificar_estoque_minimo(*, produto, saldo_atual: Decimal) -> int:
    """Cria notificações de estoque baixo para todos os usuários elegíveis.

    Dedupe por dia: se já houve alerta hoje para o mesmo produto/usuário,
    não duplica. Devolve a quantidade de notificações criadas (0 se todas
    foram puladas por dedup).
    """
    if not produto or not produto.estoque_minimo or produto.estoque_minimo <= 0:
        return 0
    if saldo_atual is None or saldo_atual > produto.estoque_minimo:
        return 0

    hoje = _hoje()
    destinatarios = usuarios_destinatarios(NotificacaoUsuario.Tipo.ESTOQUE_MINIMO)
    if not destinatarios:
        return 0

    from nucleo.units import base_unit_for_product_unit

    unidade_base = base_unit_for_product_unit(produto.unidade)
    titulo = f"Estoque baixo: {produto.sku} ({produto.nome})"
    mensagem = (
        f"O produto {produto.sku} – {produto.nome} está com saldo de "
        f"{saldo_atual} {unidade_base}, abaixo do mínimo de "
        f"{produto.estoque_minimo} {unidade_base}."
    )

    contexto_email = {
        "produto": produto,
        "saldo_atual": saldo_atual,
        "unidade_base": unidade_base,
        "link_sistema": getattr(settings, "FRONTEND_URL", ""),
    }

    criadas = 0
    for usuario in destinatarios:
        novo = criar_notificacao(
            usuario=usuario,
            tipo=NotificacaoUsuario.Tipo.ESTOQUE_MINIMO,
            titulo=titulo,
            mensagem=mensagem,
            nivel=NotificacaoUsuario.Nivel.CRITICO,
            referencia_app="estoque",
            referencia_id=produto.pk,
            data_referencia=hoje,
            enviar_email=True,
            contexto_email=contexto_email,
            template_email="estoque_minimo",
            assunto_email=f"[Gestão Artesanal] Estoque baixo: {produto.sku}",
        )
        if novo is not None:
            criadas += 1
    return criadas


def resolver_notificacoes_estoque(*, produto) -> int:
    """Marca como lidas as notificações de estoque mínimo abertas para o
    produto quando o saldo voltou ao normal.

    Devolve quantas notificações foram resolvidas.
    """
    if not produto:
        return 0
    return NotificacaoUsuario.objects.filter(
        tipo=NotificacaoUsuario.Tipo.ESTOQUE_MINIMO,
        referencia_app="estoque",
        referencia_id=produto.pk,
        lida_em__isnull=True,
    ).update(lida_em=timezone.now())


# ---------------------------------------------------------------------------
# Financeiro: vencidos + a vencer
# ---------------------------------------------------------------------------


def notificar_vencimentos_pagar(*, hoje: date | None = None, dias_a_vencer: int = DIAS_A_VENCER) -> dict:
    """Gera notificações para contas a pagar vencidas e a vencer.

    Devolve dict com totais ``{"vencidas_criadas": int, "a_vencer_criadas": int}``.
    """
    from financeiro.models import ContaPagar

    return _processar_vencimentos(
        model_cls=ContaPagar,
        rotulo_titulo="Conta a pagar",
        hoje=hoje,
        dias_a_vencer=dias_a_vencer,
        referencia_app="financeiro",
    )


def notificar_vencimentos_receber(*, hoje: date | None = None, dias_a_vencer: int = DIAS_A_VENCER) -> dict:
    """Gera notificações para contas a receber vencidas e a vencer."""
    from financeiro.models import ContaReceber

    return _processar_vencimentos(
        model_cls=ContaReceber,
        rotulo_titulo="Conta a receber",
        hoje=hoje,
        dias_a_vencer=dias_a_vencer,
        referencia_app="financeiro",
    )


def _processar_vencimentos(
    *,
    model_cls,
    rotulo_titulo: str,
    hoje: date | None,
    dias_a_vencer: int,
    referencia_app: str,
) -> dict:
    from financeiro.models import ContaPagar
    from financeiro.services import SITUACOES_EM_ABERTO_PAGAR, SITUACOES_EM_ABERTO_RECEBER

    hoje = hoje or _hoje()
    limite_alerta = hoje + timedelta(days=dias_a_vencer)
    situacoes_aberto = (
        SITUACOES_EM_ABERTO_PAGAR
        if model_cls is ContaPagar
        else SITUACOES_EM_ABERTO_RECEBER
    )

    destinatarios_vencidos = usuarios_destinatarios(NotificacaoUsuario.Tipo.TITULO_VENCIDO)
    destinatarios_a_vencer = usuarios_destinatarios(NotificacaoUsuario.Tipo.TITULO_A_VENCER)
    if not destinatarios_vencidos and not destinatarios_a_vencer:
        return {"vencidas_criadas": 0, "a_vencer_criadas": 0}

    contas_vencidas = model_cls.objects.filter(
        situacao__in=situacoes_aberto,
        vencimento__lt=hoje,
    )
    contas_a_vencer = model_cls.objects.filter(
        situacao__in=situacoes_aberto,
        vencimento__gte=hoje,
        vencimento__lte=limite_alerta,
    )

    vencidas_criadas = _criar_para_lote(
        contas=contas_vencidas,
        destinatarios=destinatarios_vencidos,
        tipo=NotificacaoUsuario.Tipo.TITULO_VENCIDO,
        nivel=NotificacaoUsuario.Nivel.CRITICO,
        rotulo_titulo=rotulo_titulo,
        descricao_status="venceu",
        referencia_app=referencia_app,
        enviar_email=True,
        template_email="titulo_vencido",
        hoje=hoje,
    )
    a_vencer_criadas = _criar_para_lote(
        contas=contas_a_vencer,
        destinatarios=destinatarios_a_vencer,
        tipo=NotificacaoUsuario.Tipo.TITULO_A_VENCER,
        nivel=NotificacaoUsuario.Nivel.AVISO,
        rotulo_titulo=rotulo_titulo,
        descricao_status="vence em breve",
        referencia_app=referencia_app,
        enviar_email=False,
        template_email=None,
        hoje=hoje,
    )

    return {
        "vencidas_criadas": vencidas_criadas,
        "a_vencer_criadas": a_vencer_criadas,
    }


def _criar_para_lote(
    *,
    contas: Iterable,
    destinatarios: list,
    tipo: str,
    nivel: str,
    rotulo_titulo: str,
    descricao_status: str,
    referencia_app: str,
    enviar_email: bool,
    template_email: str | None,
    hoje: date,
) -> int:
    """Cria notificações com dedupe para cada (conta × usuário)."""
    if not destinatarios:
        return 0
    criadas = 0
    for conta in contas:
        # Texto da mensagem (uma vez por conta).
        venc = conta.vencimento
        dias_diff = (venc - hoje).days
        if tipo == NotificacaoUsuario.Tipo.TITULO_VENCIDO:
            sufixo = f"venceu há {-dias_diff} dia(s)" if dias_diff < 0 else "vence hoje"
        else:
            sufixo = f"vence em {dias_diff} dia(s)" if dias_diff > 0 else "vence hoje"

        titulo = f"{rotulo_titulo} #{conta.pk} — {sufixo}"
        mensagem = (
            f"{rotulo_titulo} {conta.descricao} (R$ {conta.valor}) "
            f"{descricao_status} em {venc.strftime('%d/%m/%Y')}."
        )

        contexto_email = {
            "conta": conta,
            "rotulo_titulo": rotulo_titulo,
            "dias_diff": dias_diff,
            "link_sistema": getattr(settings, "FRONTEND_URL", ""),
        }

        for usuario in destinatarios:
            novo = criar_notificacao(
                usuario=usuario,
                tipo=tipo,
                titulo=titulo,
                mensagem=mensagem,
                nivel=nivel,
                referencia_app=referencia_app,
                referencia_id=conta.pk,
                data_referencia=venc,
                enviar_email=enviar_email,
                contexto_email=contexto_email,
                template_email=template_email,
                assunto_email=f"[Gestão Artesanal] {titulo}",
            )
            if novo is not None:
                criadas += 1
    return criadas
