from datetime import date
from decimal import Decimal

from django.test import TestCase

from clientes.models import Cliente
from financeiro.models import ContaReceber, LinhaContaReceber
from produtos.models import Categoria, Fornecedor, Produto
from relatorios.services import linhas_receita_por_produto, resumo_receita_por_produto


class ReceitaPorProdutoServiceTests(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(
            nome="Cliente A", documento="", telefone="", email=""
        )
        self.outro_cliente = Cliente.objects.create(
            nome="Cliente B", documento="", telefone="", email=""
        )
        self.cat_a = Categoria.objects.create(nome="CatA")
        self.cat_b = Categoria.objects.create(nome="CatB")
        self.sup = Fornecedor.objects.create(nome="Forn")
        self.p1 = Produto.objects.create(
            sku="P1",
            nome="Produto 1",
            categoria=self.cat_a,
            fornecedor=self.sup,
            unidade="UN",
            preco_venda=Decimal("10.00"),
            custo_aquisicao=Decimal("4"),
            custo_unitario=Decimal("4.00"),
        )
        self.p2 = Produto.objects.create(
            sku="P2",
            nome="Produto 2",
            categoria=self.cat_b,
            fornecedor=self.sup,
            unidade="UN",
            preco_venda=Decimal("5.00"),
            custo_aquisicao=Decimal("1"),
            custo_unitario=Decimal("1.00"),
        )

    def _line(self, ar, product, qty, unit_price, discount, line_total):
        LinhaContaReceber.objects.create(
            conta_receber=ar,
            produto=product,
            quantidade=qty,
            unidade="UN",
            preco_unitario=unit_price,
            desconto=discount,
            total_linha=line_total,
        )

    def test_aggregates_lines_and_margin(self):
        ar = ContaReceber.objects.create(
            cliente=self.cliente,
            descricao="Pedido",
            data_emissao=date(2026, 4, 10),
            valor=Decimal("30.00"),
            vencimento=date(2026, 4, 30),
            situacao=ContaReceber.Situacao.ABERTO,
        )
        self._line(ar, self.p1, Decimal("2"), Decimal("10"), Decimal("0"), Decimal("20.00"))
        self._line(ar, self.p1, Decimal("1"), Decimal("10"), Decimal("0"), Decimal("10.00"))

        rows = linhas_receita_por_produto(date(2026, 4, 1), date(2026, 4, 30))
        by_sku = {r["sku"]: r for r in rows}
        self.assertIn("P1", by_sku)
        r1 = by_sku["P1"]
        self.assertEqual(r1["quantidade_total"], Decimal("3"))
        self.assertEqual(r1["faturamento_total"], Decimal("30.00"))
        self.assertEqual(r1["custo_total"], Decimal("12.00"))
        self.assertEqual(r1["lucro"], Decimal("18.00"))
        self.assertEqual(r1["margem_percentual"], Decimal("60.00"))

    def test_respects_customer_filter(self):
        ar_a = ContaReceber.objects.create(
            cliente=self.cliente,
            descricao="A",
            data_emissao=date(2026, 4, 5),
            valor=Decimal("10"),
            vencimento=date(2026, 4, 20),
            situacao=ContaReceber.Situacao.ABERTO,
        )
        self._line(ar_a, self.p1, Decimal("1"), Decimal("10"), Decimal("0"), Decimal("10.00"))
        ar_b = ContaReceber.objects.create(
            cliente=self.outro_cliente,
            descricao="B",
            data_emissao=date(2026, 4, 5),
            valor=Decimal("10"),
            vencimento=date(2026, 4, 20),
            situacao=ContaReceber.Situacao.ABERTO,
        )
        self._line(ar_b, self.p1, Decimal("1"), Decimal("10"), Decimal("0"), Decimal("10.00"))

        rows_all = linhas_receita_por_produto(date(2026, 4, 1), date(2026, 4, 30))
        self.assertEqual(len(rows_all), 1)
        self.assertEqual(rows_all[0]["faturamento_total"], Decimal("20.00"))

        rows_a = linhas_receita_por_produto(
            date(2026, 4, 1), date(2026, 4, 30), cliente_id=self.cliente.pk
        )
        self.assertEqual(rows_a[0]["faturamento_total"], Decimal("10.00"))

    def test_excludes_cancelled_and_out_of_range(self):
        ar_ok = ContaReceber.objects.create(
            cliente=self.cliente,
            descricao="Ok",
            data_emissao=date(2026, 4, 15),
            valor=Decimal("10"),
            vencimento=date(2026, 4, 30),
            situacao=ContaReceber.Situacao.ABERTO,
        )
        self._line(ar_ok, self.p1, Decimal("1"), Decimal("10"), Decimal("0"), Decimal("10.00"))
        ar_bad = ContaReceber.objects.create(
            cliente=self.cliente,
            descricao="Cancelado",
            data_emissao=date(2026, 4, 15),
            valor=Decimal("99"),
            vencimento=date(2026, 4, 30),
            situacao=ContaReceber.Situacao.CANCELADO,
        )
        self._line(ar_bad, self.p1, Decimal("9"), Decimal("10"), Decimal("0"), Decimal("90.00"))
        ar_old = ContaReceber.objects.create(
            cliente=self.cliente,
            descricao="Fora",
            data_emissao=date(2026, 1, 1),
            valor=Decimal("5"),
            vencimento=date(2026, 1, 10),
            situacao=ContaReceber.Situacao.ABERTO,
        )
        self._line(ar_old, self.p1, Decimal("1"), Decimal("5"), Decimal("0"), Decimal("5.00"))

        rows = linhas_receita_por_produto(date(2026, 4, 1), date(2026, 4, 30))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["faturamento_total"], Decimal("10.00"))

    def test_category_filter(self):
        ar = ContaReceber.objects.create(
            cliente=self.cliente,
            descricao="Mix",
            data_emissao=date(2026, 4, 2),
            valor=Decimal("15"),
            vencimento=date(2026, 4, 20),
            situacao=ContaReceber.Situacao.RECEBIDO,
            recebido_em=date(2026, 4, 18),
        )
        self._line(ar, self.p1, Decimal("1"), Decimal("10"), Decimal("0"), Decimal("10.00"))
        self._line(ar, self.p2, Decimal("1"), Decimal("5"), Decimal("0"), Decimal("5.00"))

        rows_a = linhas_receita_por_produto(
            date(2026, 4, 1), date(2026, 4, 30), categoria_id=self.cat_a.pk
        )
        self.assertEqual(len(rows_a), 1)
        self.assertEqual(rows_a[0]["sku"], "P1")

        rows_b = linhas_receita_por_produto(
            date(2026, 4, 1), date(2026, 4, 30), categoria_id=self.cat_b.pk
        )
        self.assertEqual(len(rows_b), 1)
        self.assertEqual(rows_b[0]["sku"], "P2")

    def test_resumo_consolidates_rows(self):
        ar = ContaReceber.objects.create(
            cliente=self.cliente,
            descricao="Pedido",
            data_emissao=date(2026, 4, 10),
            valor=Decimal("30.00"),
            vencimento=date(2026, 4, 30),
            situacao=ContaReceber.Situacao.ABERTO,
        )
        self._line(ar, self.p1, Decimal("2"), Decimal("10"), Decimal("0"), Decimal("20.00"))
        self._line(ar, self.p2, Decimal("1"), Decimal("5"), Decimal("0"), Decimal("5.00"))

        linhas = linhas_receita_por_produto(date(2026, 4, 1), date(2026, 4, 30))
        resumo = resumo_receita_por_produto(linhas)
        self.assertEqual(resumo["faturamento_total"], Decimal("25.00"))
        self.assertEqual(resumo["custo_total"], Decimal("9.00"))
        self.assertEqual(resumo["lucro_total"], Decimal("16.00"))
        self.assertEqual(resumo["margem_percentual"], Decimal("64.00"))
