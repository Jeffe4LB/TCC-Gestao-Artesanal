from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.core.cache import cache
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import TruncMonth

from estoque.models import SaldoEstoque
from financeiro.models import ContaPagar, ContaReceber, LinhaContaReceber
from financeiro.services import (
    agregar_saldo_restante,
    queryset_contas_em_aberto_pagar,
    queryset_contas_em_aberto_receber,
)


def _arredondar_moeda(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _ttl_cache_relatorio() -> int:
    return int(getattr(settings, "RELATORIO_CACHE_TTL", 60))


def _ler_cache_relatorio(chave: str):
    return cache.get(chave)


def _gravar_cache_relatorio(chave: str, valor) -> None:
    cache.set(chave, valor, timeout=_ttl_cache_relatorio())


def queryset_posicao_estoque():
    return (
        SaldoEstoque.objects.select_related("produto", "produto__categoria")
        .filter(produto__ativo=True)
        .order_by("produto__sku")
    )


def queryset_estoque_baixo():
    return (
        SaldoEstoque.objects.filter(
            produto__ativo=True,
            produto__estoque_minimo__gt=0,
            quantidade__lte=F("produto__estoque_minimo"),
        )
        .select_related("produto", "produto__categoria")
        .annotate(gap=F("produto__estoque_minimo") - F("quantidade"))
        .order_by("-gap", "produto__sku")
    )


def totais_financeiro_em_aberto():
    chave = "rel:fin_aberto"
    cached = _ler_cache_relatorio(chave)
    if cached is not None:
        return cached
    pagar = queryset_contas_em_aberto_pagar()
    receber = queryset_contas_em_aberto_receber()
    resultado = {
        "contagem_pagar": pagar.count(),
        "total_pagar": agregar_saldo_restante(pagar),
        "contagem_receber": receber.count(),
        "total_receber": agregar_saldo_restante(receber),
    }
    _gravar_cache_relatorio(chave, resultado)
    return resultado


def totais_fluxo_caixa(data_de, data_ate):
    entradas = ContaReceber.objects.filter(
        situacao=ContaReceber.Situacao.RECEBIDO,
        recebido_em__gte=data_de,
        recebido_em__lte=data_ate,
    ).aggregate(t=Sum("valor"))["t"] or Decimal("0")
    saidas = ContaPagar.objects.filter(
        situacao=ContaPagar.Situacao.PAGO,
        pago_em__gte=data_de,
        pago_em__lte=data_ate,
    ).aggregate(t=Sum("valor"))["t"] or Decimal("0")
    return entradas, saidas, entradas - saidas


def faixas_envelhecimento(model_cls, hoje):
    """Agrupa lançamentos em aberto por faixa de vencimento (saldo restante)."""
    chave = f"rel:aging:{model_cls.__name__}:{hoje.isoformat()}"
    cached = _ler_cache_relatorio(chave)
    if cached is not None:
        return cached
    if model_cls is ContaPagar:
        qs = queryset_contas_em_aberto_pagar()
    else:
        qs = queryset_contas_em_aberto_receber()
    ate_7 = hoje + timedelta(days=7)
    ate_30 = hoje + timedelta(days=30)

    vencidas = qs.filter(vencimento__lt=hoje)
    vence_ate_7 = qs.filter(vencimento__gte=hoje, vencimento__lte=ate_7)
    vence_8_a_30 = qs.filter(vencimento__gt=ate_7, vencimento__lte=ate_30)
    vence_apos_30 = qs.filter(vencimento__gt=ate_30)

    def agregar(q):
        return {
            "quantidade": q.count(),
            "total": agregar_saldo_restante(q),
        }

    resultado = {
        "vencidas": agregar(vencidas),
        "vence_ate_7_dias": agregar(vence_ate_7),
        "vence_8_a_30_dias": agregar(vence_8_a_30),
        "vence_apos_30_dias": agregar(vence_apos_30),
    }
    _gravar_cache_relatorio(chave, resultado)
    return resultado


def linhas_receita_por_produto(data_de, data_ate, cliente_id=None, categoria_id=None):
    qs = LinhaContaReceber.objects.filter(
        conta_receber__data_emissao__gte=data_de,
        conta_receber__data_emissao__lte=data_ate,
        conta_receber__situacao__in=(
            ContaReceber.Situacao.ABERTO,
            ContaReceber.Situacao.RECEBIDO,
        ),
        produto_id__isnull=False,
    )
    if cliente_id:
        qs = qs.filter(conta_receber__cliente_id=cliente_id)
    if categoria_id:
        qs = qs.filter(produto__categoria_id=categoria_id)

    custo_expr = ExpressionWrapper(
        F("quantidade") * F("produto__custo_unitario"),
        output_field=DecimalField(max_digits=24, decimal_places=6),
    )

    agg = (
        qs.values(
            "produto_id",
            "produto__sku",
            "produto__nome",
            "produto__categoria__nome",
        )
        .annotate(
            quantidade_total=Sum("quantidade"),
            faturamento_total=Sum("total_linha"),
            custo_total=Sum(custo_expr),
        )
        .order_by("produto__sku")
    )

    linhas = []
    for row in agg:
        qty = row["quantidade_total"] or Decimal("0")
        faturamento = _arredondar_moeda(row["faturamento_total"] or Decimal("0"))
        custo = _arredondar_moeda(row["custo_total"] or Decimal("0"))
        lucro = _arredondar_moeda(faturamento - custo)
        margem_pct = (
            (lucro / faturamento * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if faturamento > 0
            else Decimal("0")
        )
        linhas.append(
            {
                "produto_id": row["produto_id"],
                "sku": row["produto__sku"] or "",
                "nome": row["produto__nome"] or "",
                "categoria": row["produto__categoria__nome"] or "",
                "quantidade_total": qty,
                "faturamento_total": faturamento,
                "custo_total": custo,
                "lucro": lucro,
                "margem_percentual": margem_pct,
            }
        )
    return linhas


def resumo_receita_por_produto(linhas):
    """Totais consolidados a partir das linhas agregadas por produto."""
    faturamento = sum((row["faturamento_total"] for row in linhas), Decimal("0"))
    custo = sum((row["custo_total"] for row in linhas), Decimal("0"))
    faturamento = _arredondar_moeda(faturamento)
    custo = _arredondar_moeda(custo)
    lucro = _arredondar_moeda(faturamento - custo)
    margem_pct = (
        (lucro / faturamento * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if faturamento > 0
        else Decimal("0")
    )
    return {
        "faturamento_total": faturamento,
        "custo_total": custo,
        "lucro_total": lucro,
        "margem_percentual": margem_pct,
    }


def resumo_posicao_estoque(qs):
    """Contagem de SKUs e valor estimado (quantidade × custo unitário do cadastro)."""
    valor_expr = ExpressionWrapper(
        F("quantidade") * F("produto__custo_unitario"),
        output_field=DecimalField(max_digits=24, decimal_places=6),
    )
    valor = qs.aggregate(v=Sum(valor_expr))["v"] or Decimal("0")
    return {
        "total_skus": qs.count(),
        "valor_estoque": _arredondar_moeda(valor),
    }


def resumo_movimentacoes_estoque(qs, limite_previa):
    """Contagem no período (antes do slice) e totais por tipo de movimento."""
    total_no_periodo = qs.count()
    por_tipo = (
        qs.values("tipo_movimentacao")
        .annotate(quantidade=Count("id"))
        .order_by("tipo_movimentacao")
    )
    return {
        "total_no_periodo": total_no_periodo,
        "contagem_por_tipo": {
            row["tipo_movimentacao"]: row["quantidade"] for row in por_tipo
        },
        "limite_previa": limite_previa,
        "truncado": total_no_periodo > limite_previa,
    }


_ROTULOS_MESES_PT = [
    "jan", "fev", "mar", "abr", "mai", "jun",
    "jul", "ago", "set", "out", "nov", "dez",
]


def _adicionar_meses(d: date, delta: int) -> date:
    """Soma `delta` meses a `d` (dia 1) preservando o dia 1."""
    ano = d.year + (d.month - 1 + delta) // 12
    mes = (d.month - 1 + delta) % 12 + 1
    return date(ano, mes, 1)


def fluxo_caixa_por_mes(*, hoje: date, meses: int = 12) -> list[dict]:
    chave = f"rel:fluxo_mes:{hoje.isoformat()}:{meses}"
    cached = _ler_cache_relatorio(chave)
    if cached is not None:
        return cached
    resultado = _calcular_fluxo_caixa_por_mes(hoje=hoje, meses=meses)
    _gravar_cache_relatorio(chave, resultado)
    return resultado


def _calcular_fluxo_caixa_por_mes(*, hoje: date, meses: int = 12) -> list[dict]:
    """Entradas, saídas e líquido por mês para os últimos N meses.

    Considera apenas lançamentos efetivamente quitados (entradas: `recebido_em`;
    saídas: `pago_em`). Preenche os meses sem movimento com zeros, garantindo
    `meses` linhas no resultado mesmo se o banco estiver vazio.

    O dicionário de cada mês contém:

    - `mes`: ``"YYYY-MM-01"`` (chave estável para ordenação no front)
    - `mes_rotulo`: ``"jan/2026"`` (PT-BR, para eixo X)
    - `entradas`, `saidas`, `liquido`: ``str`` com 2 casas decimais
    """
    meses = max(1, min(int(meses), 60))
    primeiro_mes = _adicionar_meses(hoje.replace(day=1), -(meses - 1))
    fim_intervalo = _adicionar_meses(primeiro_mes, meses) - timedelta(days=1)

    entradas = (
        ContaReceber.objects.filter(
            situacao=ContaReceber.Situacao.RECEBIDO,
            recebido_em__gte=primeiro_mes,
            recebido_em__lte=fim_intervalo,
        )
        .annotate(mes=TruncMonth("recebido_em"))
        .values("mes")
        .annotate(total=Sum("valor"))
    )
    saidas = (
        ContaPagar.objects.filter(
            situacao=ContaPagar.Situacao.PAGO,
            pago_em__gte=primeiro_mes,
            pago_em__lte=fim_intervalo,
        )
        .annotate(mes=TruncMonth("pago_em"))
        .values("mes")
        .annotate(total=Sum("valor"))
    )

    entradas_por_mes: dict[date, Decimal] = {row["mes"]: row["total"] or Decimal("0") for row in entradas}
    saidas_por_mes: dict[date, Decimal] = {row["mes"]: row["total"] or Decimal("0") for row in saidas}

    resultado: list[dict] = []
    for i in range(meses):
        chave = _adicionar_meses(primeiro_mes, i)
        ent = _arredondar_moeda(entradas_por_mes.get(chave, Decimal("0")))
        sai = _arredondar_moeda(saidas_por_mes.get(chave, Decimal("0")))
        liq = _arredondar_moeda(ent - sai)
        resultado.append(
            {
                "mes": chave.isoformat(),
                "mes_rotulo": f"{_ROTULOS_MESES_PT[chave.month - 1]}/{chave.year}",
                "entradas": str(ent),
                "saidas": str(sai),
                "liquido": str(liq),
            }
        )
    return resultado


def estoque_por_categoria() -> list[dict]:
    chave = "rel:estoque_categoria"
    cached = _ler_cache_relatorio(chave)
    if cached is not None:
        return cached
    resultado = _calcular_estoque_por_categoria()
    _gravar_cache_relatorio(chave, resultado)
    return resultado


def _calcular_estoque_por_categoria() -> list[dict]:
    """Saldo de estoque agregado por categoria de produto.

    Retorna lista ordenada por valor estimado decrescente. Cada item contém:

    - `categoria`: nome da categoria (`"Sem categoria"` quando o produto não tem)
    - `total_skus`: quantidade de SKUs naquela categoria
    - `quantidade_total`: ``str`` (3 casas decimais)
    - `valor_estoque`: ``str`` (2 casas decimais, R$)

    Apenas produtos ativos contribuem para a agregação.
    """
    valor_expr = ExpressionWrapper(
        F("quantidade") * F("produto__custo_unitario"),
        output_field=DecimalField(max_digits=24, decimal_places=6),
    )
    agg = (
        SaldoEstoque.objects.filter(produto__ativo=True)
        .values("produto__categoria__nome")
        .annotate(
            total_skus=Count("produto_id", distinct=True),
            quantidade_total=Sum("quantidade"),
            valor_total=Sum(valor_expr),
        )
        .order_by("-valor_total")
    )

    linhas: list[dict] = []
    for row in agg:
        nome = row["produto__categoria__nome"] or "Sem categoria"
        qtd = row["quantidade_total"] or Decimal("0")
        valor = _arredondar_moeda(row["valor_total"] or Decimal("0"))
        linhas.append(
            {
                "categoria": nome,
                "total_skus": int(row["total_skus"] or 0),
                "quantidade_total": str(qtd.quantize(Decimal("0.001"))),
                "valor_estoque": str(valor),
            }
        )
    return linhas


# Aliases legados
stock_position_queryset = queryset_posicao_estoque
low_stock_queryset = queryset_estoque_baixo
finance_open_totals = totais_financeiro_em_aberto
cash_flow_totals = totais_fluxo_caixa
aging_buckets = faixas_envelhecimento
revenue_by_product_rows = linhas_receita_por_produto
