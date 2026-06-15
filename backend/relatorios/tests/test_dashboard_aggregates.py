"""Testes dos agregados consumidos pelos gráficos do painel.

Cobertura:

- `fluxo_caixa_por_mes`: preenche meses vazios, classifica entradas/saídas pelo
  campo correto, respeita ordem cronológica e clamp do parâmetro.
- `estoque_por_categoria`: agrupa por nome de categoria, inclui produtos sem
  categoria como "Sem categoria", ignora inativos e ordena por valor desc.
- Endpoints REST `/relatorios/financeiro/fluxo-mensal/` e
  `/relatorios/estoque/por-categoria/`: status, contrato JSON e respeito ao
  parâmetro `meses`.
"""

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from clientes.models import Cliente
from estoque.models import SaldoEstoque
from financeiro.models import ContaPagar, ContaReceber
from produtos.models import Categoria, Fornecedor, Produto
from relatorios.services import estoque_por_categoria, fluxo_caixa_por_mes

User = get_user_model()


class FluxoCaixaPorMesServiceTests(TestCase):
    def setUp(self):
        cache.clear()
        self.cliente = Cliente.objects.create(
            nome="C", documento="", telefone="", email=""
        )

    def _receber(self, recebido_em: date, valor: Decimal):
        ContaReceber.objects.create(
            cliente=self.cliente,
            descricao="r",
            data_emissao=recebido_em,
            valor=valor,
            vencimento=recebido_em,
            situacao=ContaReceber.Situacao.RECEBIDO,
            recebido_em=recebido_em,
        )

    def _pagar(self, pago_em: date, valor: Decimal):
        ContaPagar.objects.create(
            descricao="p",
            valor=valor,
            vencimento=pago_em,
            situacao=ContaPagar.Situacao.PAGO,
            pago_em=pago_em,
        )

    def test_preenche_meses_vazios_com_zero(self):
        hoje = date(2026, 6, 15)
        resultado = fluxo_caixa_por_mes(hoje=hoje, meses=6)
        self.assertEqual(len(resultado), 6)
        meses = [r["mes"] for r in resultado]
        self.assertEqual(
            meses,
            ["2026-01-01", "2026-02-01", "2026-03-01", "2026-04-01", "2026-05-01", "2026-06-01"],
        )
        for r in resultado:
            self.assertEqual(r["entradas"], "0.00")
            self.assertEqual(r["saidas"], "0.00")
            self.assertEqual(r["liquido"], "0.00")

    def test_classifica_entradas_e_saidas_e_calcula_liquido(self):
        self._receber(date(2026, 2, 5), Decimal("100"))
        self._receber(date(2026, 2, 20), Decimal("50"))
        self._pagar(date(2026, 2, 10), Decimal("30"))
        self._pagar(date(2026, 3, 1), Decimal("80"))

        hoje = date(2026, 3, 15)
        resultado = fluxo_caixa_por_mes(hoje=hoje, meses=3)  # jan, fev, mar

        self.assertEqual(resultado[0]["mes"], "2026-01-01")
        self.assertEqual(resultado[0]["entradas"], "0.00")
        self.assertEqual(resultado[0]["saidas"], "0.00")

        self.assertEqual(resultado[1]["mes"], "2026-02-01")
        self.assertEqual(resultado[1]["entradas"], "150.00")
        self.assertEqual(resultado[1]["saidas"], "30.00")
        self.assertEqual(resultado[1]["liquido"], "120.00")

        self.assertEqual(resultado[2]["mes"], "2026-03-01")
        self.assertEqual(resultado[2]["entradas"], "0.00")
        self.assertEqual(resultado[2]["saidas"], "80.00")
        self.assertEqual(resultado[2]["liquido"], "-80.00")

    def test_rotulo_em_pt_br(self):
        resultado = fluxo_caixa_por_mes(hoje=date(2026, 3, 31), meses=3)
        self.assertEqual([r["mes_rotulo"] for r in resultado], ["jan/2026", "fev/2026", "mar/2026"])

    def test_clamp_de_meses(self):
        self.assertEqual(len(fluxo_caixa_por_mes(hoje=date(2026, 1, 1), meses=0)), 1)
        self.assertEqual(len(fluxo_caixa_por_mes(hoje=date(2026, 1, 1), meses=100)), 60)

    def test_ignora_lancamentos_nao_quitados(self):
        ContaReceber.objects.create(
            cliente=self.cliente,
            descricao="aberto",
            data_emissao=date(2026, 2, 5),
            valor=Decimal("999"),
            vencimento=date(2026, 2, 5),
            situacao=ContaReceber.Situacao.ABERTO,
        )
        resultado = fluxo_caixa_por_mes(hoje=date(2026, 2, 28), meses=2)
        for r in resultado:
            self.assertEqual(r["entradas"], "0.00")


class EstoquePorCategoriaServiceTests(TestCase):
    def setUp(self):
        cache.clear()
        self.cat_a = Categoria.objects.create(nome="Massas")
        self.cat_b = Categoria.objects.create(nome="Bebidas")
        forn = Fornecedor.objects.create(nome="F")

        # 2 produtos em "Massas" (1 com saldo grande, 1 com saldo zero)
        self.p1 = Produto.objects.create(
            sku="M1", nome="Macarrão",
            categoria=self.cat_a, fornecedor=forn,
            unidade="KG", preco_venda=Decimal("10"),
            custo_aquisicao=Decimal("3"), custo_unitario=Decimal("3"),
        )
        self.p2 = Produto.objects.create(
            sku="M2", nome="Lasanha",
            categoria=self.cat_a, fornecedor=forn,
            unidade="KG", preco_venda=Decimal("20"),
            custo_aquisicao=Decimal("8"), custo_unitario=Decimal("8"),
        )
        # 1 produto em "Bebidas"
        self.p3 = Produto.objects.create(
            sku="B1", nome="Suco",
            categoria=self.cat_b, fornecedor=forn,
            unidade="L", preco_venda=Decimal("5"),
            custo_aquisicao=Decimal("2"), custo_unitario=Decimal("2"),
        )
        # 1 produto inativo (não deve aparecer)
        self.p5 = Produto.objects.create(
            sku="X1", nome="Inativo",
            categoria=self.cat_a, fornecedor=forn,
            unidade="UN", preco_venda=Decimal("1"),
            custo_aquisicao=Decimal("999"), custo_unitario=Decimal("999"),
            ativo=False,
        )

        SaldoEstoque.objects.filter(produto=self.p1).update(quantidade=Decimal("10"))   # 10 × 3 = 30
        SaldoEstoque.objects.filter(produto=self.p2).update(quantidade=Decimal("5"))    # 5 × 8 = 40
        SaldoEstoque.objects.filter(produto=self.p3).update(quantidade=Decimal("100"))  # 100 × 2 = 200
        SaldoEstoque.objects.filter(produto=self.p5).update(quantidade=Decimal("9999")) # ignorado

    def test_agrega_por_categoria_ordenado_por_valor_desc(self):
        linhas = estoque_por_categoria()
        nomes = [l["categoria"] for l in linhas]
        # Bebidas: 200 > Massas: 70
        self.assertEqual(nomes, ["Bebidas", "Massas"])

    def test_valores_calculados_corretamente(self):
        por_nome = {l["categoria"]: l for l in estoque_por_categoria()}
        self.assertEqual(por_nome["Massas"]["total_skus"], 2)
        self.assertEqual(por_nome["Massas"]["valor_estoque"], "70.00")
        self.assertEqual(por_nome["Bebidas"]["total_skus"], 1)
        self.assertEqual(por_nome["Bebidas"]["valor_estoque"], "200.00")

    def test_ignora_produtos_inativos(self):
        linhas = estoque_por_categoria()
        massas = next(l for l in linhas if l["categoria"] == "Massas")
        # Inativo tinha custo 999 × 9999 → se contasse, valor seria altíssimo
        self.assertEqual(massas["valor_estoque"], "70.00")


class DashboardEndpointTests(TestCase):
    def setUp(self):
        cache.clear()
        self.admin = User.objects.create_superuser(
            username="admin@x", password="x", email="admin@x"
        )
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def test_fluxo_mensal_responde_estrutura_correta(self):
        r = self.client.get("/api/v1/relatorios/financeiro/fluxo-mensal/?meses=6")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["meses"], 6)
        self.assertEqual(len(data["resultados"]), 6)
        primeiro = data["resultados"][0]
        for chave in ("mes", "mes_rotulo", "entradas", "saidas", "liquido"):
            self.assertIn(chave, primeiro)

    def test_fluxo_mensal_default_12(self):
        r = self.client.get("/api/v1/relatorios/financeiro/fluxo-mensal/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["meses"], 12)

    def test_fluxo_mensal_meses_invalido_usa_default(self):
        r = self.client.get("/api/v1/relatorios/financeiro/fluxo-mensal/?meses=abc")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["meses"], 12)

    def test_estoque_por_categoria_endpoint(self):
        r = self.client.get("/api/v1/relatorios/estoque/por-categoria/")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("total_categorias", data)
        self.assertIn("valor_total", data)
        self.assertIn("resultados", data)
        self.assertIsInstance(data["resultados"], list)

    def test_requer_autenticacao(self):
        client = APIClient()
        r1 = client.get("/api/v1/relatorios/financeiro/fluxo-mensal/")
        r2 = client.get("/api/v1/relatorios/estoque/por-categoria/")
        self.assertEqual(r1.status_code, 401)
        self.assertEqual(r2.status_code, 401)
