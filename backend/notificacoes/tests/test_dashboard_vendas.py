from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from clientes.models import Cliente
from financeiro.models import ContaReceber, LinhaContaReceber
from notificacoes.services import montar_vendas_produto_painel
from produtos.models import Categoria, Fornecedor, Produto


class VendasProdutoPainelTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="painel", password="Passw0rd!")
        self.client.force_authenticate(self.user)

        self.cliente = Cliente.objects.create(
            nome="Cliente A", documento="", telefone="", email=""
        )
        cat = Categoria.objects.create(nome="CatA")
        sup = Fornecedor.objects.create(nome="Forn")
        self.p1 = Produto.objects.create(
            sku="P1",
            nome="Produto 1",
            categoria=cat,
            fornecedor=sup,
            unidade="UN",
            preco_venda=Decimal("10.00"),
            custo_aquisicao=Decimal("4"),
            custo_unitario=Decimal("4.00"),
        )
        self.p2 = Produto.objects.create(
            sku="P2",
            nome="Produto 2",
            categoria=cat,
            fornecedor=sup,
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

    def test_montar_vendas_produto_painel_totals_and_top(self):
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

        payload = montar_vendas_produto_painel(date(2026, 4, 1), date(2026, 4, 30), top_limit=5)
        self.assertEqual(payload["resumo"]["lucro_total"], "16.00")
        self.assertEqual(payload["resumo"]["faturamento_total"], "25.00")
        self.assertEqual(payload["resumo"]["total_produtos"], 2)
        self.assertEqual(len(payload["top_produtos"]), 2)
        self.assertEqual(payload["top_produtos"][0]["sku"], "P1")

    def test_resumo_endpoint_includes_vendas_when_period_sent(self):
        ar = ContaReceber.objects.create(
            cliente=self.cliente,
            descricao="Pedido",
            data_emissao=date(2026, 4, 10),
            valor=Decimal("10.00"),
            vencimento=date(2026, 4, 30),
            situacao=ContaReceber.Situacao.ABERTO,
        )
        self._line(ar, self.p1, Decimal("1"), Decimal("10"), Decimal("0"), Decimal("10.00"))

        r = self.client.get(
            "/api/v1/notificacoes/resumo/?from=2026-04-01&to=2026-04-30",
            format="json",
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("vendas_por_produto", body)
        self.assertEqual(body["vendas_por_produto"]["resumo"]["lucro_total"], "6.00")
        self.assertEqual(len(body["vendas_por_produto"]["top_produtos"]), 1)

    def test_resumo_omits_vendas_without_period(self):
        r = self.client.get("/api/v1/notificacoes/resumo/", format="json")
        self.assertEqual(r.status_code, 200)
        self.assertNotIn("vendas_por_produto", r.json())
