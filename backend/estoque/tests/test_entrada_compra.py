from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from estoque.models import MovimentacaoEstoque, SaldoEstoque
from financeiro.models import ContaPagar, LinhaContaPagar
from produtos.models import Categoria, Fornecedor, Produto

User = get_user_model()


class EntradaCompraIntegrationTests(TestCase):
    def setUp(self):
        self.cat = Categoria.objects.create(nome="Mat")
        self.sup = Fornecedor.objects.create(nome="Forn")
        self.p1 = Produto.objects.create(
            sku="INS-A",
            nome="Insumo A",
            categoria=self.cat,
            fornecedor=self.sup,
            tipo_produto=Produto.TipoProduto.COMPRADO,
            unidade="KG",
            preco_venda=Decimal("0"),
            custo_aquisicao=Decimal("10.00"),
            custo_unitario=Decimal("10.00"),
        )
        self.p2 = Produto.objects.create(
            sku="INS-B",
            nome="Insumo B",
            categoria=self.cat,
            fornecedor=self.sup,
            tipo_produto=Produto.TipoProduto.COMPRADO,
            unidade="UN",
            preco_venda=Decimal("0"),
            custo_aquisicao=Decimal("2.50"),
            custo_unitario=Decimal("2.50"),
        )
        self.user = User.objects.create_user(username="compras", password="x")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_entrada_compra_cria_uma_conta_tres_movimentos(self):
        res = self.client.post(
            "/api/v1/entradas-compra/",
            {
                "fornecedor": self.sup.pk,
                "descricao": "NF 1001",
                "vencimento": "2026-06-01",
                "linhas": [
                    {
                        "produto": self.p1.pk,
                        "quantidade": "2",
                        "unidade": "KG",
                    },
                    {
                        "produto": self.p2.pk,
                        "quantidade": "4",
                        "unidade": "UN",
                    },
                ],
            },
            format="json",
        )
        self.assertEqual(res.status_code, 201, res.data)
        payable_id = res.data["conta_pagar"]["id"]
        self.assertEqual(ContaPagar.objects.count(), 1)
        payable = ContaPagar.objects.get(pk=payable_id)
        self.assertEqual(payable.valor, Decimal("30.00"))
        self.assertEqual(LinhaContaPagar.objects.filter(conta_pagar=payable).count(), 2)
        self.assertEqual(
            MovimentacaoEstoque.objects.filter(
                conta_pagar=payable,
                tipo_movimentacao=MovimentacaoEstoque.TipoMovimentacao.ENTRADA_COMPRA,
            ).count(),
            2,
        )
        b1 = SaldoEstoque.objects.get(produto=self.p1)
        b2 = SaldoEstoque.objects.get(produto=self.p2)
        self.assertEqual(b1.quantidade, Decimal("2"))
        self.assertEqual(b2.quantidade, Decimal("4"))

    def test_rejeita_produto_fabricado(self):
        fab = Produto.objects.create(
            sku="FAB-X",
            nome="Fab",
            categoria=self.cat,
            tipo_produto=Produto.TipoProduto.FABRICADO,
            unidade="UN",
            preco_venda=Decimal("20"),
            custo_aquisicao=Decimal("0"),
        )
        res = self.client.post(
            "/api/v1/entradas-compra/",
            {
                "descricao": "Teste",
                "vencimento": "2026-06-01",
                "linhas": [{"produto": fab.pk, "quantidade": "1", "unidade": "UN"}],
            },
            format="json",
        )
        self.assertEqual(res.status_code, 400)
