from datetime import date
from decimal import Decimal

from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from estoque.models import MovimentacaoEstoque
from financeiro.models import ContaPagar, ContaReceber
from nucleo.api_enums import (
    TIPO_MOVIMENTACAO_DO_API,
    tipo_movimentacao_do_api,
    tipo_movimentacao_para_api,
)
from nucleo.permissions import TemCapacidade
from nucleo.units import base_unit_for_product_unit

from . import services
from .exportadores import (
    DocumentoRelatorio,
    SecaoTabela,
    formatar_intervalo,
    formato_solicitado,
    nome_usuario,
    resposta_pdf,
    resposta_xlsx,
)
from .utils import parsear_parametro_data, resposta_csv, resposta_csv_linhas, texto_decimal

_MSG_DATAS_OBRIGATORIAS = "Informe as datas inicial e final (AAAA-MM-DD)."
_MSG_ORDEM_DATAS = "A data inicial não pode ser posterior à data final."
_CSV_COL_CODIGO = "Código (SKU)"

_ROTULOS_FAIXA_ENVELHECIMENTO = {
    "vencidas": "Vencidas",
    "vence_ate_7_dias": "Vence em até 7 dias",
    "vence_8_a_30_dias": "Vence em 8 a 30 dias",
    "vence_apos_30_dias": "Vence após 30 dias",
}


def _rotulo_tipo_movimentacao(codigo: str) -> str:
    return dict(MovimentacaoEstoque.TipoMovimentacao.choices).get(codigo, codigo)


def _rotulo_tipo_api(api_code: str) -> str:
    """Converte código de API (snake_case PT) para rótulo legível."""
    bd_code = TIPO_MOVIMENTACAO_DO_API.get(api_code, api_code)
    return _rotulo_tipo_movimentacao(bd_code)


class _RelatorioView(APIView):
    permission_classes = [IsAuthenticated, TemCapacidade]
    required_capability = "relatorios"


# ---------------------------------------------------------------------------
# Posição de estoque
# ---------------------------------------------------------------------------


class RelatorioPosicaoEstoqueView(_RelatorioView):
    """Posição de estoque (saldos ativos)."""

    NOME_ARQUIVO = "relatorio-posicao-estoque"

    def get(self, request):
        qs = services.queryset_posicao_estoque()
        cid = request.query_params.get("categoria") or request.query_params.get("category")
        if cid:
            qs = qs.filter(produto__categoria_id=cid)
        if search := request.query_params.get("search"):
            qs = qs.filter(
                Q(produto__sku__icontains=search) | Q(produto__nome__icontains=search)
            )

        rows_data = []
        for b in qs:
            p = b.produto
            abaixo = p.estoque_minimo > 0 and b.quantidade <= p.estoque_minimo
            rows_data.append(
                {
                    "sku": p.sku,
                    "nome": p.nome,
                    "categoria": p.categoria.nome if p.categoria_id else "",
                    "quantidade": texto_decimal(b.quantidade),
                    "unidade_base": base_unit_for_product_unit(p.unidade),
                    "estoque_minimo": texto_decimal(p.estoque_minimo),
                    "abaixo_minimo": abaixo,
                }
            )

        resumo = services.resumo_posicao_estoque(qs)

        formato = formato_solicitado(request)
        if formato == "csv":
            csv_rows = [
                [
                    r["sku"],
                    r["nome"],
                    r["categoria"],
                    r["quantidade"],
                    r["estoque_minimo"],
                    "Sim" if r["abaixo_minimo"] else "Não",
                ]
                for r in rows_data
            ]
            csv_rows.extend(
                [
                    [],
                    ["Resumo"],
                    ["SKUs listados", str(resumo["total_skus"])],
                    ["Valor estoque (R$)", texto_decimal(resumo["valor_estoque"])],
                ]
            )
            return resposta_csv(
                f"{self.NOME_ARQUIVO}.csv",
                [_CSV_COL_CODIGO, "Nome", "Categoria", "Saldo", "Estoque mín.", "Abaixo do mín.?"],
                csv_rows,
            )

        if formato in ("pdf", "xlsx"):
            documento = self._montar_documento(rows_data, resumo)
            if formato == "pdf":
                return resposta_pdf(self.NOME_ARQUIVO, documento, usuario=nome_usuario(request))
            return resposta_xlsx(self.NOME_ARQUIVO, documento)

        return Response(
            {
                "total": len(rows_data),
                "resumo": {
                    "total_skus": resumo["total_skus"],
                    "valor_estoque": texto_decimal(resumo["valor_estoque"]),
                },
                "resultados": rows_data,
            }
        )

    def _montar_documento(self, rows_data, resumo) -> DocumentoRelatorio:
        linhas = [
            [
                r["sku"],
                r["nome"],
                r["categoria"] or "—",
                f"{r['quantidade']} {r['unidade_base']}",
                r["estoque_minimo"],
                "Sim" if r["abaixo_minimo"] else "Não",
            ]
            for r in rows_data
        ]
        return DocumentoRelatorio(
            titulo="Posição de estoque",
            subtitulo="Saldos ativos por produto",
            resumo=[
                ("SKUs listados", str(resumo["total_skus"])),
                ("Valor estoque (R$)", texto_decimal(resumo["valor_estoque"])),
            ],
            secoes=[
                SecaoTabela(
                    cabecalhos=[
                        _CSV_COL_CODIGO,
                        "Nome",
                        "Categoria",
                        "Saldo",
                        "Estoque mín.",
                        "Abaixo do mín.?",
                    ],
                    linhas=linhas,
                    alinhamentos=["L", "L", "L", "R", "R", "C"],
                )
            ],
        )


# ---------------------------------------------------------------------------
# Movimentações de estoque
# ---------------------------------------------------------------------------


class RelatorioMovimentacoesEstoqueView(_RelatorioView):
    """Movimentações de estoque por período (data do lançamento)."""

    NOME_ARQUIVO = "relatorio-movimentacoes-estoque"

    def get(self, request):
        from_s = request.query_params.get("from")
        to_s = request.query_params.get("to")
        data_de = parsear_parametro_data(from_s)
        data_ate = parsear_parametro_data(to_s)
        if not data_de or not data_ate:
            return Response(
                {"detail": _MSG_DATAS_OBRIGATORIAS},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if data_de > data_ate:
            return Response(
                {"detail": _MSG_ORDEM_DATAS},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = MovimentacaoEstoque.objects.select_related("produto", "criado_por").filter(
            criado_em__date__gte=data_de,
            criado_em__date__lte=data_ate,
        )
        pid = request.query_params.get("produto") or request.query_params.get("product")
        if pid:
            qs = qs.filter(produto_id=pid)
        mt_raw = request.query_params.get("tipo_movimentacao") or request.query_params.get(
            "movement_type"
        )
        if mt_raw:
            try:
                qs = qs.filter(tipo_movimentacao=tipo_movimentacao_do_api(mt_raw))
            except Exception:
                qs = qs.none()

        qs = qs.order_by("-criado_em", "-id")

        formato = formato_solicitado(request)
        if not formato:
            try:
                limit = min(int(request.query_params.get("limit", 500)), 2000)
            except (TypeError, ValueError):
                limit = 500
        else:
            limit = 10000

        resumo_raw = services.resumo_movimentacoes_estoque(qs, limit)
        qs_lista = qs[:limit]

        rows_data = []
        for m in qs_lista:
            rows_data.append(
                {
                    "id": m.id,
                    "criado_em": m.criado_em.isoformat(),
                    "sku": m.produto.sku,
                    "nome_produto": m.produto.nome,
                    "delta_quantidade": texto_decimal(m.delta_quantidade),
                    "unidade_base": base_unit_for_product_unit(m.produto.unidade),
                    "tipo_movimentacao": tipo_movimentacao_para_api(m.tipo_movimentacao),
                    "criado_por_nome": m.criado_por.username if m.criado_por_id else None,
                    "observacoes": m.observacoes,
                }
            )

        contagem_por_tipo = {
            tipo_movimentacao_para_api(codigo): qtd
            for codigo, qtd in resumo_raw["contagem_por_tipo"].items()
        }
        resumo_payload = {
            "total_no_periodo": resumo_raw["total_no_periodo"],
            "contagem_por_tipo": contagem_por_tipo,
            "limite_previa": resumo_raw["limite_previa"],
            "truncado": resumo_raw["truncado"],
        }

        if formato == "csv":
            csv_rows = [
                [
                    r["id"],
                    r["criado_em"],
                    r["sku"],
                    r["nome_produto"],
                    r["delta_quantidade"],
                    _rotulo_tipo_api(r["tipo_movimentacao"]),
                    r["criado_por_nome"] or "",
                    r["observacoes"],
                ]
                for r in rows_data
            ]
            csv_rows.extend([[], ["Resumo do período (todos os lançamentos)"]])
            csv_rows.append(
                ["Total de movimentações", str(resumo_raw["total_no_periodo"])]
            )
            csv_rows.append(["Linhas neste arquivo", str(len(rows_data))])
            for codigo, qtd in resumo_raw["contagem_por_tipo"].items():
                api_code = tipo_movimentacao_para_api(codigo)
                csv_rows.append([_rotulo_tipo_api(api_code), str(qtd)])
            return resposta_csv(
                f"{self.NOME_ARQUIVO}.csv",
                [
                    "Nº",
                    "Data/hora",
                    _CSV_COL_CODIGO,
                    "Produto",
                    "Variação",
                    "Tipo",
                    "Responsável",
                    "Obs.",
                ],
                csv_rows,
            )

        if formato in ("pdf", "xlsx"):
            documento = self._montar_documento(rows_data, resumo_raw, data_de, data_ate)
            if formato == "pdf":
                return resposta_pdf(self.NOME_ARQUIVO, documento, usuario=nome_usuario(request))
            return resposta_xlsx(self.NOME_ARQUIVO, documento)

        return Response(
            {
                "de": data_de.isoformat(),
                "ate": data_ate.isoformat(),
                "total": len(rows_data),
                "resumo": resumo_payload,
                "resultados": rows_data,
            }
        )

    def _montar_documento(self, rows_data, resumo_raw, data_de, data_ate) -> DocumentoRelatorio:
        linhas_principais = [
            [
                r["id"],
                r["criado_em"].replace("T", " ")[:16],
                r["sku"],
                r["nome_produto"],
                f"{r['delta_quantidade']} {r['unidade_base']}",
                _rotulo_tipo_api(r["tipo_movimentacao"]),
                (r["criado_por_nome"] or "—")[:40],
                (r["observacoes"] or "")[:80],
            ]
            for r in rows_data
        ]

        secoes: list[SecaoTabela] = [
            SecaoTabela(
                titulo="Movimentações",
                cabecalhos=[
                    "Nº",
                    "Data/hora",
                    _CSV_COL_CODIGO,
                    "Produto",
                    "Variação",
                    "Tipo",
                    "Responsável",
                    "Obs.",
                ],
                linhas=linhas_principais,
                alinhamentos=["R", "L", "L", "L", "R", "L", "L", "L"],
            ),
        ]

        if resumo_raw["contagem_por_tipo"]:
            linhas_resumo = [
                [_rotulo_tipo_api(tipo_movimentacao_para_api(codigo)), qtd]
                for codigo, qtd in resumo_raw["contagem_por_tipo"].items()
            ]
            secoes.append(
                SecaoTabela(
                    titulo="Contagem por tipo de movimento",
                    cabecalhos=["Tipo", "Quantidade"],
                    linhas=linhas_resumo,
                    alinhamentos=["L", "R"],
                )
            )

        truncado_aviso = (
            f" (mostrando primeiras {len(linhas_principais)} linhas)"
            if resumo_raw["truncado"]
            else ""
        )
        return DocumentoRelatorio(
            titulo="Movimentações de estoque",
            subtitulo="Lançamentos de entrada, saída e produção" + truncado_aviso,
            periodo=formatar_intervalo(data_de, data_ate),
            resumo=[
                ("Total no período", str(resumo_raw["total_no_periodo"])),
                ("Linhas listadas", str(len(rows_data))),
            ],
            secoes=secoes,
            orientacao_paisagem=True,
        )


# ---------------------------------------------------------------------------
# Estoque abaixo do mínimo
# ---------------------------------------------------------------------------


class RelatorioEstoqueAbaixoMinimoView(_RelatorioView):
    """Produtos com saldo ≤ mínimo (mesma regra do alerta de estoque)."""

    NOME_ARQUIVO = "relatorio-estoque-abaixo-minimo"

    def get(self, request):
        qs = services.queryset_estoque_baixo()
        if search := request.query_params.get("search"):
            qs = qs.filter(
                Q(produto__sku__icontains=search) | Q(produto__nome__icontains=search)
            )

        rows_data = []
        for b in qs:
            p = b.produto
            rows_data.append(
                {
                    "sku": p.sku,
                    "nome": p.nome,
                    "estoque_minimo": texto_decimal(p.estoque_minimo),
                    "quantidade_atual": texto_decimal(b.quantidade),
                    "unidade_base": base_unit_for_product_unit(p.unidade),
                    "gap": texto_decimal(b.gap),
                }
            )

        formato = formato_solicitado(request)
        if formato == "csv":
            csv_rows = [
                [r["sku"], r["nome"], r["estoque_minimo"], r["quantidade_atual"], r["gap"]]
                for r in rows_data
            ]
            return resposta_csv(
                f"{self.NOME_ARQUIVO}.csv",
                [_CSV_COL_CODIGO, "Nome", "Mínimo", "Saldo atual", "Falta p/ mínimo"],
                csv_rows,
            )

        if formato in ("pdf", "xlsx"):
            documento = self._montar_documento(rows_data)
            if formato == "pdf":
                return resposta_pdf(self.NOME_ARQUIVO, documento, usuario=nome_usuario(request))
            return resposta_xlsx(self.NOME_ARQUIVO, documento)

        return Response(
            {
                "total": len(rows_data),
                "resumo": {"itens_criticos": len(rows_data)},
                "resultados": rows_data,
            }
        )

    def _montar_documento(self, rows_data) -> DocumentoRelatorio:
        linhas = [
            [
                r["sku"],
                r["nome"],
                f"{r['estoque_minimo']} {r['unidade_base']}",
                f"{r['quantidade_atual']} {r['unidade_base']}",
                f"{r['gap']} {r['unidade_base']}",
            ]
            for r in rows_data
        ]
        return DocumentoRelatorio(
            titulo="Estoque abaixo do mínimo",
            subtitulo="Itens com saldo igual ou inferior ao estoque mínimo cadastrado",
            resumo=[("Itens críticos", str(len(rows_data)))],
            secoes=[
                SecaoTabela(
                    cabecalhos=[_CSV_COL_CODIGO, "Nome", "Mínimo", "Saldo atual", "Falta"],
                    linhas=linhas,
                    alinhamentos=["L", "L", "R", "R", "R"],
                    mensagem_vazio="Nenhum item abaixo do mínimo.",
                )
            ],
        )


# ---------------------------------------------------------------------------
# Financeiro em aberto
# ---------------------------------------------------------------------------


class RelatorioFinanceiroEmAbertoView(_RelatorioView):
    """Contas em aberto + totais."""

    NOME_ARQUIVO = "relatorio-financeiro-em-aberto"

    def get(self, request):
        from financeiro.services import queryset_contas_em_aberto_pagar, queryset_contas_em_aberto_receber

        pagar = (
            queryset_contas_em_aberto_pagar()
            .select_related("fornecedor")
            .order_by("vencimento")
        )
        receber = (
            queryset_contas_em_aberto_receber()
            .select_related("cliente")
            .order_by("vencimento")
        )

        lista_pagar = [
            {
                "id": x.id,
                "descricao": x.descricao,
                "valor": texto_decimal(x.valor),
                "valor_pago": texto_decimal(x.valor_pago),
                "saldo_restante": texto_decimal(x.saldo_restante),
                "vencimento": x.vencimento.isoformat(),
                "fornecedor": x.fornecedor.nome if x.fornecedor_id else None,
                "rotulo_parcela": (
                    f"{x.numero_parcela}/{x.total_parcelas}" if x.documento_id else None
                ),
            }
            for x in pagar
        ]
        lista_receber = [
            {
                "id": x.id,
                "descricao": x.descricao,
                "valor": texto_decimal(x.valor),
                "valor_pago": texto_decimal(x.valor_pago),
                "saldo_restante": texto_decimal(x.saldo_restante),
                "vencimento": x.vencimento.isoformat(),
                "cliente": x.cliente.nome if x.cliente_id else None,
                "rotulo_parcela": (
                    f"{x.numero_parcela}/{x.total_parcelas}" if x.documento_id else None
                ),
            }
            for x in receber
        ]

        totais = services.totais_financeiro_em_aberto()

        payload = {
            "resumo": {
                "contagem_pagar": totais["contagem_pagar"],
                "total_pagar": texto_decimal(totais["total_pagar"]),
                "contagem_receber": totais["contagem_receber"],
                "total_receber": texto_decimal(totais["total_receber"]),
                "saldo_liquido": texto_decimal(
                    totais["total_receber"] - totais["total_pagar"]
                ),
            },
            "contas_pagar": lista_pagar,
            "contas_receber": lista_receber,
        }

        formato = formato_solicitado(request)
        if formato == "csv":
            rows_p = [
                [p["id"], p["descricao"], p["valor"], p["vencimento"], p["fornecedor"] or ""]
                for p in lista_pagar
            ]
            rows_r = [
                [p["id"], p["descricao"], p["valor"], p["vencimento"], p["cliente"] or ""]
                for p in lista_receber
            ]
            all_rows = [
                ["Resumo"],
                ["Total a pagar (R$)", texto_decimal(totais["total_pagar"]), "Qtd.", str(totais["contagem_pagar"])],
                ["Total a receber (R$)", texto_decimal(totais["total_receber"]), "Qtd.", str(totais["contagem_receber"])],
                [],
                ["Contas a pagar (em aberto)"],
                ["Cód.", "Descrição", "Valor", "Vencimento", "Fornecedor"],
            ]
            all_rows.extend(rows_p)
            all_rows.extend(
                [[], ["Contas a receber (em aberto)"], ["Cód.", "Descrição", "Valor", "Vencimento", "Cliente"]]
            )
            all_rows.extend(rows_r)
            return resposta_csv_linhas(f"{self.NOME_ARQUIVO}.csv", all_rows)

        if formato in ("pdf", "xlsx"):
            documento = self._montar_documento(lista_pagar, lista_receber, totais)
            if formato == "pdf":
                return resposta_pdf(self.NOME_ARQUIVO, documento, usuario=nome_usuario(request))
            return resposta_xlsx(self.NOME_ARQUIVO, documento)

        return Response(payload)

    def _montar_documento(self, lista_pagar, lista_receber, totais) -> DocumentoRelatorio:
        linhas_p = [
            [p["id"], p["descricao"], p["valor"], p["vencimento"], p["fornecedor"] or "—"]
            for p in lista_pagar
        ]
        linhas_r = [
            [r["id"], r["descricao"], r["valor"], r["vencimento"], r["cliente"] or "—"]
            for r in lista_receber
        ]
        saldo_liquido = totais["total_receber"] - totais["total_pagar"]
        return DocumentoRelatorio(
            titulo="Financeiro em aberto",
            subtitulo="Contas a pagar e a receber não quitadas",
            resumo=[
                ("Contas a pagar — quantidade", str(totais["contagem_pagar"])),
                ("Contas a pagar — total (R$)", texto_decimal(totais["total_pagar"])),
                ("Contas a receber — quantidade", str(totais["contagem_receber"])),
                ("Contas a receber — total (R$)", texto_decimal(totais["total_receber"])),
                ("Saldo líquido (R$)", texto_decimal(saldo_liquido)),
            ],
            secoes=[
                SecaoTabela(
                    titulo="Contas a pagar (em aberto)",
                    cabecalhos=["Cód.", "Descrição", "Valor", "Vencimento", "Fornecedor"],
                    linhas=linhas_p,
                    alinhamentos=["R", "L", "R", "C", "L"],
                    mensagem_vazio="Nenhuma conta a pagar em aberto.",
                ),
                SecaoTabela(
                    titulo="Contas a receber (em aberto)",
                    cabecalhos=["Cód.", "Descrição", "Valor", "Vencimento", "Cliente"],
                    linhas=linhas_r,
                    alinhamentos=["R", "L", "R", "C", "L"],
                    mensagem_vazio="Nenhuma conta a receber em aberto.",
                ),
            ],
        )


# ---------------------------------------------------------------------------
# Fluxo de caixa
# ---------------------------------------------------------------------------


class RelatorioFluxoCaixaView(_RelatorioView):
    """Fluxo de caixa no período (mesma regra do módulo financeiro)."""

    NOME_ARQUIVO = "relatorio-fluxo-caixa"

    def get(self, request):
        from_s = request.query_params.get("from")
        to_s = request.query_params.get("to")
        data_de = parsear_parametro_data(from_s)
        data_ate = parsear_parametro_data(to_s)
        if not data_de or not data_ate:
            return Response(
                {"detail": _MSG_DATAS_OBRIGATORIAS},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if data_de > data_ate:
            return Response(
                {"detail": _MSG_ORDEM_DATAS},
                status=status.HTTP_400_BAD_REQUEST,
            )

        entradas, saidas, liquido = services.totais_fluxo_caixa(data_de, data_ate)
        payload = {
            "de": data_de.isoformat(),
            "ate": data_ate.isoformat(),
            "entradas": texto_decimal(entradas),
            "saidas": texto_decimal(saidas),
            "liquido": texto_decimal(liquido),
        }

        formato = formato_solicitado(request)
        if formato == "csv":
            return resposta_csv_linhas(
                f"{self.NOME_ARQUIVO}.csv",
                [
                    ["Período", payload["de"], "até", payload["ate"]],
                    ["Entradas (recebimentos)", payload["entradas"]],
                    ["Saídas (pagamentos)", payload["saidas"]],
                    ["Saldo do período", payload["liquido"]],
                ],
            )

        if formato in ("pdf", "xlsx"):
            documento = self._montar_documento(entradas, saidas, liquido, data_de, data_ate)
            if formato == "pdf":
                return resposta_pdf(self.NOME_ARQUIVO, documento, usuario=nome_usuario(request))
            return resposta_xlsx(self.NOME_ARQUIVO, documento)

        return Response(payload)

    def _montar_documento(
        self,
        entradas: Decimal,
        saidas: Decimal,
        liquido: Decimal,
        data_de: date,
        data_ate: date,
    ) -> DocumentoRelatorio:
        return DocumentoRelatorio(
            titulo="Fluxo de caixa",
            subtitulo="Entradas e saídas efetivamente realizadas no período",
            periodo=formatar_intervalo(data_de, data_ate),
            resumo=[
                ("Entradas (R$)", texto_decimal(entradas)),
                ("Saídas (R$)", texto_decimal(saidas)),
                ("Saldo do período (R$)", texto_decimal(liquido)),
            ],
            secoes=[
                SecaoTabela(
                    cabecalhos=["Categoria", "Valor (R$)"],
                    linhas=[
                        ["Entradas (recebimentos)", texto_decimal(entradas)],
                        ["Saídas (pagamentos)", texto_decimal(saidas)],
                    ],
                    totais=["Saldo do período", texto_decimal(liquido)],
                    alinhamentos=["L", "R"],
                )
            ],
        )


# ---------------------------------------------------------------------------
# Envelhecimento financeiro
# ---------------------------------------------------------------------------


class RelatorioEnvelhecimentoFinanceiroView(_RelatorioView):
    """Envelhecimento simples de títulos em aberto por faixa de vencimento."""

    NOME_ARQUIVO = "relatorio-envelhecimento"

    def get(self, request):
        hoje = timezone.now().date()

        faixas_pagar = services.faixas_envelhecimento(ContaPagar, hoje)
        faixas_receber = services.faixas_envelhecimento(ContaReceber, hoje)

        def fmt_faixa(b):
            return {"quantidade": b["quantidade"], "total": texto_decimal(b["total"])}

        payload = {
            "hoje": hoje.isoformat(),
            "pagar": {k: fmt_faixa(v) for k, v in faixas_pagar.items()},
            "receber": {k: fmt_faixa(v) for k, v in faixas_receber.items()},
        }

        formato = formato_solicitado(request)
        if formato == "csv":
            rows = [
                ["Data base", payload["hoje"]],
                [],
                ["Contas a pagar (em aberto)"],
                ["Faixa", "Quantidade", "Total (R$)"],
            ]
            for key, label in _ROTULOS_FAIXA_ENVELHECIMENTO.items():
                b = faixas_pagar[key]
                rows.append([label, str(b["quantidade"]), texto_decimal(b["total"])])
            rows.extend([[], ["Contas a receber (em aberto)"], ["Faixa", "Quantidade", "Total (R$)"]])
            for key, label in _ROTULOS_FAIXA_ENVELHECIMENTO.items():
                b = faixas_receber[key]
                rows.append([label, str(b["quantidade"]), texto_decimal(b["total"])])
            return resposta_csv_linhas(f"{self.NOME_ARQUIVO}.csv", rows)

        if formato in ("pdf", "xlsx"):
            documento = self._montar_documento(hoje, faixas_pagar, faixas_receber)
            if formato == "pdf":
                return resposta_pdf(self.NOME_ARQUIVO, documento, usuario=nome_usuario(request))
            return resposta_xlsx(self.NOME_ARQUIVO, documento)

        return Response(payload)

    def _montar_documento(self, hoje, faixas_pagar, faixas_receber) -> DocumentoRelatorio:
        def construir_linhas(faixas):
            return [
                [label, faixas[key]["quantidade"], texto_decimal(faixas[key]["total"])]
                for key, label in _ROTULOS_FAIXA_ENVELHECIMENTO.items()
            ]

        def total(faixas):
            return sum((faixas[k]["total"] for k in faixas), Decimal("0"))

        return DocumentoRelatorio(
            titulo="Envelhecimento financeiro",
            subtitulo=f"Títulos em aberto por faixa de vencimento (base: {hoje.strftime('%d/%m/%Y')})",
            resumo=[
                ("Total a pagar (R$)", texto_decimal(total(faixas_pagar))),
                ("Total a receber (R$)", texto_decimal(total(faixas_receber))),
            ],
            secoes=[
                SecaoTabela(
                    titulo="Contas a pagar",
                    cabecalhos=["Faixa", "Quantidade", "Total (R$)"],
                    linhas=construir_linhas(faixas_pagar),
                    alinhamentos=["L", "R", "R"],
                ),
                SecaoTabela(
                    titulo="Contas a receber",
                    cabecalhos=["Faixa", "Quantidade", "Total (R$)"],
                    linhas=construir_linhas(faixas_receber),
                    alinhamentos=["L", "R", "R"],
                ),
            ],
        )


# ---------------------------------------------------------------------------
# Receita por produto
# ---------------------------------------------------------------------------


def _inteiro_positivo_opcional(raw, rotulo: str):
    if raw is None or raw == "":
        return None, None
    try:
        v = int(raw)
    except ValueError:
        return None, f"Parâmetro {rotulo} inválido."
    if v < 1:
        return None, f"Parâmetro {rotulo} deve ser um id positivo."
    return v, None


class RelatorioReceitaPorProdutoView(_RelatorioView):
    """Faturamento e margem por produto (linhas de contas a receber, data de emissão)."""

    NOME_ARQUIVO = "relatorio-receita-por-produto"

    def get(self, request):
        from_s = request.query_params.get("from")
        to_s = request.query_params.get("to")
        data_de = parsear_parametro_data(from_s)
        data_ate = parsear_parametro_data(to_s)
        if not data_de or not data_ate:
            return Response(
                {"detail": _MSG_DATAS_OBRIGATORIAS},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if data_de > data_ate:
            return Response(
                {"detail": _MSG_ORDEM_DATAS},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cliente_raw = request.query_params.get("cliente") or request.query_params.get("customer")
        cliente_id, err = _inteiro_positivo_opcional(cliente_raw, "cliente")
        if err:
            return Response({"detail": err}, status=status.HTTP_400_BAD_REQUEST)
        categoria_raw = request.query_params.get("categoria") or request.query_params.get("category")
        categoria_id, err = _inteiro_positivo_opcional(categoria_raw, "categoria")
        if err:
            return Response({"detail": err}, status=status.HTTP_400_BAD_REQUEST)

        linhas = services.linhas_receita_por_produto(
            data_de, data_ate, cliente_id=cliente_id, categoria_id=categoria_id
        )
        resumo = services.resumo_receita_por_produto(linhas)

        rows_data = []
        for r in linhas:
            rows_data.append(
                {
                    "id_produto": r["produto_id"],
                    "sku": r["sku"],
                    "nome": r["nome"],
                    "categoria": r["categoria"],
                    "quantidade": texto_decimal(r["quantidade_total"]),
                    "faturamento_total": texto_decimal(r["faturamento_total"]),
                    "custo_total": texto_decimal(r["custo_total"]),
                    "lucro": texto_decimal(r["lucro"]),
                    "margem_percentual": texto_decimal(r["margem_percentual"]),
                }
            )

        formato = formato_solicitado(request)
        if formato == "csv":
            csv_rows = [
                [
                    r["sku"],
                    r["nome"],
                    r["categoria"],
                    r["quantidade"],
                    r["faturamento_total"],
                    r["custo_total"],
                    r["lucro"],
                    r["margem_percentual"],
                ]
                for r in rows_data
            ]
            csv_rows.extend(
                [
                    [],
                    [
                        "TOTAIS",
                        "",
                        "",
                        "",
                        texto_decimal(resumo["faturamento_total"]),
                        texto_decimal(resumo["custo_total"]),
                        texto_decimal(resumo["lucro_total"]),
                        texto_decimal(resumo["margem_percentual"]),
                    ],
                ]
            )
            return resposta_csv(
                f"{self.NOME_ARQUIVO}.csv",
                [
                    _CSV_COL_CODIGO,
                    "Produto",
                    "Categoria",
                    "Qtd vendida",
                    "Faturamento (R$)",
                    "Custo (R$)",
                    "Margem (R$)",
                    "Margem %",
                ],
                csv_rows,
            )

        if formato in ("pdf", "xlsx"):
            documento = self._montar_documento(rows_data, resumo, data_de, data_ate)
            if formato == "pdf":
                return resposta_pdf(self.NOME_ARQUIVO, documento, usuario=nome_usuario(request))
            return resposta_xlsx(self.NOME_ARQUIVO, documento)

        return Response(
            {
                "de": data_de.isoformat(),
                "ate": data_ate.isoformat(),
                "total": len(rows_data),
                "resumo": {
                    "faturamento_total": texto_decimal(resumo["faturamento_total"]),
                    "custo_total": texto_decimal(resumo["custo_total"]),
                    "lucro_total": texto_decimal(resumo["lucro_total"]),
                    "margem_percentual": texto_decimal(resumo["margem_percentual"]),
                },
                "resultados": rows_data,
            }
        )

    def _montar_documento(self, rows_data, resumo, data_de, data_ate) -> DocumentoRelatorio:
        linhas = [
            [
                r["sku"],
                r["nome"],
                r["categoria"] or "—",
                r["quantidade"],
                r["faturamento_total"],
                r["custo_total"],
                r["lucro"],
                f"{r['margem_percentual']}%",
            ]
            for r in rows_data
        ]
        totais = [
            "TOTAL",
            "",
            "",
            "",
            texto_decimal(resumo["faturamento_total"]),
            texto_decimal(resumo["custo_total"]),
            texto_decimal(resumo["lucro_total"]),
            f"{texto_decimal(resumo['margem_percentual'])}%",
        ]
        return DocumentoRelatorio(
            titulo="Receita por produto",
            subtitulo="Faturamento, custo e margem por produto (linhas de contas a receber)",
            periodo=formatar_intervalo(data_de, data_ate),
            resumo=[
                ("Faturamento total (R$)", texto_decimal(resumo["faturamento_total"])),
                ("Custo total (R$)", texto_decimal(resumo["custo_total"])),
                ("Lucro total (R$)", texto_decimal(resumo["lucro_total"])),
                ("Margem média (%)", texto_decimal(resumo["margem_percentual"])),
            ],
            secoes=[
                SecaoTabela(
                    cabecalhos=[
                        _CSV_COL_CODIGO,
                        "Produto",
                        "Categoria",
                        "Qtd",
                        "Faturamento",
                        "Custo",
                        "Margem (R$)",
                        "Margem %",
                    ],
                    linhas=linhas,
                    totais=totais,
                    alinhamentos=["L", "L", "L", "R", "R", "R", "R", "R"],
                )
            ],
            orientacao_paisagem=True,
        )


# ---------------------------------------------------------------------------
# Dashboard: agregados para gráficos
# ---------------------------------------------------------------------------


class RelatorioFluxoMensalView(_RelatorioView):
    """Fluxo de caixa agregado por mês (últimos N meses).

    Apenas leitura. Não tem CSV/PDF/XLSX — é consumido pelo gráfico do painel.
    Query: ``?meses=12`` (mín. 1, máx. 60).
    """

    NOME_ARQUIVO = "relatorio-fluxo-mensal"

    def get(self, request):
        try:
            meses = int(request.query_params.get("meses", 12))
        except (TypeError, ValueError):
            meses = 12
        meses = max(1, min(meses, 60))

        dados = services.fluxo_caixa_por_mes(hoje=timezone.localdate(), meses=meses)
        return Response({"meses": meses, "resultados": dados})


class RelatorioEstoquePorCategoriaView(_RelatorioView):
    """Saldo de estoque agregado por categoria de produto."""

    NOME_ARQUIVO = "relatorio-estoque-por-categoria"

    def get(self, request):
        linhas = services.estoque_por_categoria()
        total_valor = sum((Decimal(l["valor_estoque"]) for l in linhas), Decimal("0"))
        return Response(
            {
                "total_categorias": len(linhas),
                "valor_total": texto_decimal(total_valor),
                "resultados": linhas,
            }
        )


# Aliases legados (imports externos)
_ReportView = _RelatorioView
ReportStockPositionView = RelatorioPosicaoEstoqueView
ReportStockMovementsView = RelatorioMovimentacoesEstoqueView
ReportStockLowView = RelatorioEstoqueAbaixoMinimoView
ReportFinanceOpenView = RelatorioFinanceiroEmAbertoView
ReportFinanceCashFlowView = RelatorioFluxoCaixaView
ReportFinanceAgingView = RelatorioEnvelhecimentoFinanceiroView
ReportRevenueByProductView = RelatorioReceitaPorProdutoView
