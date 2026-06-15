from datetime import timedelta

from django.db.models import Count
from django.utils import timezone

from relatorios.services import (
    linhas_receita_por_produto,
    low_stock_queryset,
    resumo_receita_por_produto,
)
from relatorios.utils import texto_decimal

from .models import NotificacaoUsuario


def montar_vendas_produto_painel(data_de, data_ate, *, top_limit: int = 10) -> dict:
    """Top produtos por lucro + totais do período (mesma regra do relatório)."""
    limite = max(1, min(top_limit, 50))
    linhas = linhas_receita_por_produto(data_de, data_ate)
    resumo = resumo_receita_por_produto(linhas)
    ordenadas = sorted(linhas, key=lambda row: row["lucro"], reverse=True)

    return {
        "de": data_de.isoformat(),
        "ate": data_ate.isoformat(),
        "resumo": {
            "faturamento_total": texto_decimal(resumo["faturamento_total"]),
            "custo_total": texto_decimal(resumo["custo_total"]),
            "lucro_total": texto_decimal(resumo["lucro_total"]),
            "margem_percentual": texto_decimal(resumo["margem_percentual"]),
            "total_produtos": len(linhas),
        },
        "top_produtos": [
            {
                "sku": row["sku"],
                "nome": row["nome"],
                "faturamento_total": texto_decimal(row["faturamento_total"]),
                "lucro": texto_decimal(row["lucro"]),
                "margem_percentual": texto_decimal(row["margem_percentual"]),
            }
            for row in ordenadas[:limite]
        ],
    }


def contar_notificacoes_nao_lidas(usuario) -> dict:
    """Conta notificações persistidas não-lidas do usuário (total + por tipo)."""
    if not usuario or not getattr(usuario, "pk", None):
        return {"total": 0, "por_tipo": {}}
    qs = NotificacaoUsuario.objects.filter(usuario=usuario, lida_em__isnull=True)
    por_tipo = {
        row["tipo"]: row["qtd"]
        for row in qs.values("tipo").annotate(qtd=Count("id")).order_by("tipo")
    }
    return {"total": qs.count(), "por_tipo": por_tipo}


def montar_resumo_notificacoes(
    *,
    days_ahead: int = 7,
    stock_preview_limit: int = 10,
    data_de=None,
    data_ate=None,
    usuario=None,
) -> dict:
    """Agrega alertas de estoque + financeiro para o painel (MVP)."""
    today = timezone.now().date()
    until = today + timedelta(days=days_ahead)

    low = low_stock_queryset()
    previa_estoque = []
    for b in low[:stock_preview_limit]:
        p = b.produto
        previa_estoque.append(
            {
                "sku": p.sku,
                "nome": p.nome,
                "estoque_minimo": str(p.estoque_minimo),
                "quantidade_atual": str(b.quantidade),
                "gap": str(b.gap),
            }
        )

    from financeiro.services import (
        agregar_saldo_restante,
        queryset_contas_em_aberto_pagar,
        queryset_contas_em_aberto_receber,
    )

    op = queryset_contas_em_aberto_pagar().filter(vencimento__lt=today)
    ore = queryset_contas_em_aberto_receber().filter(vencimento__lt=today)
    vencidos = {
        "contagem_pagar": op.count(),
        "total_pagar": str(agregar_saldo_restante(op)),
        "contagem_receber": ore.count(),
        "total_receber": str(agregar_saldo_restante(ore)),
    }

    dsp = queryset_contas_em_aberto_pagar().filter(
        vencimento__gte=today,
        vencimento__lte=until,
    )
    dsr = queryset_contas_em_aberto_receber().filter(
        vencimento__gte=today,
        vencimento__lte=until,
    )
    a_vencer = {
        "contagem_pagar": dsp.count(),
        "contagem_receber": dsr.count(),
    }

    payload = {
        "gerado_em": timezone.now().isoformat(),
        "estoque_abaixo_minimo": {
            "quantidade": low.count(),
            "previa": previa_estoque,
        },
        "financeiro": {
            "hoje": today.isoformat(),
            "ate": until.isoformat(),
            "dias_a_frente": days_ahead,
            "vencidos": vencidos,
            "a_vencer": a_vencer,
        },
    }

    if data_de and data_ate and data_de <= data_ate:
        payload["vendas_por_produto"] = montar_vendas_produto_painel(data_de, data_ate)

    if usuario is not None:
        payload["notificacoes_persistidas"] = contar_notificacoes_nao_lidas(usuario)

    return payload


# Alias legado
build_notification_summary = montar_resumo_notificacoes
