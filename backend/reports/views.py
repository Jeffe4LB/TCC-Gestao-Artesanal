from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import HasCapability

from finance.models import AccountPayable, AccountReceivable
from stock.models import StockMovement

from . import services
from .utils import csv_response, csv_response_rows, decimal_str, parse_date_param


class _ReportView(APIView):
    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = "reports"


def _want_csv(request) -> bool:
    # Não usar `format=csv`: o DRF reserva "format" para negociação de renderer e retorna 404
    # se não existir renderer com .format == "csv".
    return request.query_params.get("export", "").lower() == "csv"


class ReportStockPositionView(_ReportView):
    """Posição de estoque (saldos ativos)."""

    def get(self, request):
        qs = services.stock_position_queryset()
        if cid := request.query_params.get("category"):
            qs = qs.filter(product__category_id=cid)
        if search := request.query_params.get("search"):
            qs = qs.filter(
                Q(product__sku__icontains=search) | Q(product__name__icontains=search)
            )

        rows_data = []
        for b in qs:
            p = b.product
            below = p.min_stock > 0 and b.quantity <= p.min_stock
            rows_data.append(
                {
                    "sku": p.sku,
                    "name": p.name,
                    "category": p.category.name if p.category_id else "",
                    "quantity": decimal_str(b.quantity),
                    "min_stock": decimal_str(p.min_stock),
                    "below_minimum": below,
                }
            )

        if _want_csv(request):
            csv_rows = [
                [
                    r["sku"],
                    r["name"],
                    r["category"],
                    r["quantity"],
                    r["min_stock"],
                    "Sim" if r["below_minimum"] else "Não",
                ]
                for r in rows_data
            ]
            return csv_response(
                "relatorio-posicao-estoque.csv",
                ["SKU", "Nome", "Categoria", "Saldo", "Estoque mín.", "Abaixo do mín.?"],
                csv_rows,
            )

        return Response({"count": len(rows_data), "results": rows_data})


class ReportStockMovementsView(_ReportView):
    """Movimentações de estoque por período (data do lançamento)."""

    def get(self, request):
        from_s = request.query_params.get("from")
        to_s = request.query_params.get("to")
        date_from = parse_date_param(from_s)
        date_to = parse_date_param(to_s)
        if not date_from or not date_to:
            return Response(
                {"detail": "Informe from e to (YYYY-MM-DD)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if date_from > date_to:
            return Response(
                {"detail": "from não pode ser maior que to."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = StockMovement.objects.select_related("product").filter(
            created_at__date__gte=date_from,
            created_at__date__lte=date_to,
        )
        if pid := request.query_params.get("product"):
            qs = qs.filter(product_id=pid)
        if mt := request.query_params.get("movement_type"):
            qs = qs.filter(movement_type=mt)

        qs = qs.order_by("-created_at", "-id")

        is_csv = _want_csv(request)
        if not is_csv:
            try:
                limit = min(int(request.query_params.get("limit", 500)), 2000)
            except (TypeError, ValueError):
                limit = 500
            qs = qs[:limit]
        else:
            qs = qs[:10000]

        rows_data = []
        for m in qs:
            rows_data.append(
                {
                    "id": m.id,
                    "created_at": m.created_at.isoformat(),
                    "sku": m.product.sku,
                    "product_name": m.product.name,
                    "quantity_delta": decimal_str(m.quantity_delta),
                    "movement_type": m.movement_type,
                    "notes": m.notes,
                }
            )

        if _want_csv(request):
            csv_rows = [
                [
                    r["id"],
                    r["created_at"],
                    r["sku"],
                    r["product_name"],
                    r["quantity_delta"],
                    r["movement_type"],
                    r["notes"],
                ]
                for r in rows_data
            ]
            return csv_response(
                "relatorio-movimentacoes-estoque.csv",
                [
                    "ID",
                    "Data/hora",
                    "SKU",
                    "Produto",
                    "Variação",
                    "Tipo",
                    "Obs.",
                ],
                csv_rows,
            )

        return Response(
            {
                "from": date_from.isoformat(),
                "to": date_to.isoformat(),
                "count": len(rows_data),
                "results": rows_data,
            }
        )


class ReportStockLowView(_ReportView):
    """Produtos com saldo ≤ mínimo (mesma regra do alerta de estoque)."""

    def get(self, request):
        qs = services.low_stock_queryset()
        if search := request.query_params.get("search"):
            qs = qs.filter(
                Q(product__sku__icontains=search) | Q(product__name__icontains=search)
            )

        rows_data = []
        for b in qs:
            p = b.product
            rows_data.append(
                {
                    "sku": p.sku,
                    "name": p.name,
                    "min_stock": decimal_str(p.min_stock),
                    "current_quantity": decimal_str(b.quantity),
                    "gap": decimal_str(b.gap),
                }
            )

        if _want_csv(request):
            csv_rows = [
                [r["sku"], r["name"], r["min_stock"], r["current_quantity"], r["gap"]]
                for r in rows_data
            ]
            return csv_response(
                "relatorio-estoque-abaixo-minimo.csv",
                ["SKU", "Nome", "Mínimo", "Saldo atual", "Falta p/ mínimo"],
                csv_rows,
            )

        return Response({"count": len(rows_data), "results": rows_data})


class ReportFinanceOpenView(_ReportView):
    """Contas em aberto + totais."""

    def get(self, request):
        payables = (
            AccountPayable.objects.filter(status=AccountPayable.Status.OPEN)
            .select_related("supplier")
            .order_by("due_date")
        )
        receivables = (
            AccountReceivable.objects.filter(status=AccountReceivable.Status.OPEN)
            .select_related("customer")
            .order_by("due_date")
        )

        pay_list = [
            {
                "id": x.id,
                "description": x.description,
                "amount": decimal_str(x.amount),
                "due_date": x.due_date.isoformat(),
                "supplier": x.supplier.name if x.supplier_id else None,
            }
            for x in payables
        ]
        rec_list = [
            {
                "id": x.id,
                "description": x.description,
                "amount": decimal_str(x.amount),
                "due_date": x.due_date.isoformat(),
                "customer": x.customer.name if x.customer_id else None,
            }
            for x in receivables
        ]

        totals = services.finance_open_totals()

        payload = {
            "summary": {
                "payables_count": totals["payables_count"],
                "payables_total": decimal_str(totals["payables_total"]),
                "receivables_count": totals["receivables_count"],
                "receivables_total": decimal_str(totals["receivables_total"]),
                "net_open": decimal_str(
                    totals["receivables_total"] - totals["payables_total"]
                ),
            },
            "payables": pay_list,
            "receivables": rec_list,
        }

        if _want_csv(request):
            rows_p = [
                [p["id"], p["description"], p["amount"], p["due_date"], p["supplier"] or ""]
                for p in pay_list
            ]
            rows_r = [
                [p["id"], p["description"], p["amount"], p["due_date"], p["customer"] or ""]
                for p in rec_list
            ]
            all_rows = [
                ["Resumo"],
                [
                    "Total a pagar (R$)",
                    decimal_str(totals["payables_total"]),
                    "Qtd.",
                    str(totals["payables_count"]),
                ],
                [
                    "Total a receber (R$)",
                    decimal_str(totals["receivables_total"]),
                    "Qtd.",
                    str(totals["receivables_count"]),
                ],
                [],
                ["Contas a pagar (em aberto)"],
                ["ID", "Descrição", "Valor", "Vencimento", "Fornecedor"],
            ]
            all_rows.extend(rows_p)
            all_rows.extend([[], ["Contas a receber (em aberto)"], ["ID", "Descrição", "Valor", "Vencimento", "Cliente"]])
            all_rows.extend(rows_r)
            return csv_response_rows("relatorio-financeiro-em-aberto.csv", all_rows)

        return Response(payload)


class ReportFinanceCashFlowView(_ReportView):
    """Fluxo de caixa no período (mesma regra do módulo financeiro)."""

    def get(self, request):
        from_s = request.query_params.get("from")
        to_s = request.query_params.get("to")
        date_from = parse_date_param(from_s)
        date_to = parse_date_param(to_s)
        if not date_from or not date_to:
            return Response(
                {"detail": "Informe from e to (YYYY-MM-DD)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if date_from > date_to:
            return Response(
                {"detail": "from não pode ser maior que to."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        inf, outf, net = services.cash_flow_totals(date_from, date_to)
        payload = {
            "from": date_from.isoformat(),
            "to": date_to.isoformat(),
            "inflows": decimal_str(inf),
            "outflows": decimal_str(outf),
            "net": decimal_str(net),
        }

        if _want_csv(request):
            return csv_response_rows(
                "relatorio-fluxo-caixa.csv",
                [
                    ["Período", payload["from"], "até", payload["to"]],
                    ["Entradas (recebimentos)", payload["inflows"]],
                    ["Saídas (pagamentos)", payload["outflows"]],
                    ["Saldo do período", payload["net"]],
                ],
            )

        return Response(payload)


class ReportFinanceAgingView(_ReportView):
    """Envelhecimento simples de títulos em aberto por faixa de vencimento."""

    def get(self, request):
        today = timezone.now().date()

        pay_buckets = services.aging_buckets(AccountPayable, today)
        rec_buckets = services.aging_buckets(AccountReceivable, today)

        def fmt_bucket(b):
            return {"count": b["count"], "total": decimal_str(b["total"])}

        payload = {
            "today": today.isoformat(),
            "payables": {k: fmt_bucket(v) for k, v in pay_buckets.items()},
            "receivables": {k: fmt_bucket(v) for k, v in rec_buckets.items()},
        }

        if _want_csv(request):
            rows = [
                ["Data base", payload["today"]],
                [],
                ["Contas a pagar (em aberto)"],
                ["Faixa", "Quantidade", "Total (R$)"],
            ]
            labels = {
                "overdue": "Vencidas",
                "due_next_7_days": "Vence em até 7 dias",
                "due_8_to_30_days": "Vence em 8 a 30 dias",
                "due_after_30_days": "Vence após 30 dias",
            }
            for key, label in labels.items():
                b = pay_buckets[key]
                rows.append([label, str(b["count"]), decimal_str(b["total"])])
            rows.extend([[], ["Contas a receber (em aberto)"], ["Faixa", "Quantidade", "Total (R$)"]])
            for key, label in labels.items():
                b = rec_buckets[key]
                rows.append([label, str(b["count"]), decimal_str(b["total"])])
            return csv_response_rows("relatorio-envelhecimento.csv", rows)

        return Response(payload)


def _optional_positive_int(request, name: str):
    raw = request.query_params.get(name)
    if raw is None or raw == "":
        return None, None
    try:
        v = int(raw)
    except ValueError:
        return None, f"Parâmetro {name} inválido."
    if v < 1:
        return None, f"Parâmetro {name} deve ser um id positivo."
    return v, None


class ReportRevenueByProductView(_ReportView):
    """Faturamento e margem por produto (linhas de contas a receber, data de emissão)."""

    def get(self, request):
        from_s = request.query_params.get("from")
        to_s = request.query_params.get("to")
        date_from = parse_date_param(from_s)
        date_to = parse_date_param(to_s)
        if not date_from or not date_to:
            return Response(
                {"detail": "Informe from e to (YYYY-MM-DD)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if date_from > date_to:
            return Response(
                {"detail": "from não pode ser maior que to."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        customer_id, err = _optional_positive_int(request, "customer")
        if err:
            return Response({"detail": err}, status=status.HTTP_400_BAD_REQUEST)
        category_id, err = _optional_positive_int(request, "category")
        if err:
            return Response({"detail": err}, status=status.HTTP_400_BAD_REQUEST)

        rows = services.revenue_by_product_rows(
            date_from, date_to, customer_id=customer_id, category_id=category_id
        )

        rows_data = []
        for r in rows:
            rows_data.append(
                {
                    "product_id": r["product_id"],
                    "sku": r["sku"],
                    "name": r["name"],
                    "category": r["category"],
                    "quantity": decimal_str(r["quantity_total"]),
                    "sales_total": decimal_str(r["sales_total"]),
                    "cost_total": decimal_str(r["cost_total"]),
                    "profit": decimal_str(r["profit"]),
                    "margin_percent": decimal_str(r["margin_percent"]),
                }
            )

        if _want_csv(request):
            csv_rows = [
                [
                    r["sku"],
                    r["name"],
                    r["category"],
                    r["quantity"],
                    r["sales_total"],
                    r["cost_total"],
                    r["profit"],
                    r["margin_percent"],
                ]
                for r in rows_data
            ]
            return csv_response(
                "relatorio-receita-por-produto.csv",
                [
                    "SKU",
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

        return Response(
            {
                "from": date_from.isoformat(),
                "to": date_to.isoformat(),
                "count": len(rows_data),
                "results": rows_data,
            }
        )
