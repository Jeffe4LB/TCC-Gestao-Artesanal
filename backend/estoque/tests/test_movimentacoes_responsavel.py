from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from estoque.models import MovimentacaoEstoque, SaldoEstoque
from produtos.costs import finalizar_custo_unitario_produto
from produtos.models import Categoria, Fornecedor, Produto

User = get_user_model()


class MovimentacaoResponsavelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="operador_est", password="x")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.cat = Categoria.objects.create(nome="Mat")
        self.sup = Fornecedor.objects.create(nome="F")
        self.produto = Produto.objects.create(
            sku="MOV-RESP",
            nome="Item teste",
            categoria=self.cat,
            fornecedor=self.sup,
            tipo_produto=Produto.TipoProduto.COMPRADO,
            unidade="UN",
            preco_venda=Decimal("10.00"),
            custo_aquisicao=Decimal("5.00"),
            custo_unitario=Decimal("0"),
        )
        finalizar_custo_unitario_produto(self.produto)
        SaldoEstoque.objects.update_or_create(
            produto=self.produto,
            defaults={"quantidade": Decimal("10.000")},
        )

    def test_listagem_retorna_criado_por_nome(self):
        res = self.client.post(
            "/api/v1/movimentacoes-estoque/",
            {
                "tipo_movimentacao": "ajuste",
                "produto": self.produto.pk,
                "quantidade": "1",
                "unidade": "UN",
                "observacoes": "teste responsável",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 201, res.content)
        self.assertEqual(res.data["criado_por_nome"], "operador_est")

        list_res = self.client.get("/api/v1/movimentacoes-estoque/")
        self.assertEqual(list_res.status_code, 200)
        item = next(r for r in list_res.data["resultados"] if r["id"] == res.data["id"])
        self.assertEqual(item["criado_por_nome"], "operador_est")

    def test_movimento_sem_usuario_retorna_nome_nulo(self):
        mov = MovimentacaoEstoque.objects.create(
            produto=self.produto,
            delta_quantidade=Decimal("1"),
            tipo_movimentacao=MovimentacaoEstoque.TipoMovimentacao.AJUSTE,
            criado_por=None,
        )
        list_res = self.client.get("/api/v1/movimentacoes-estoque/")
        self.assertEqual(list_res.status_code, 200)
        item = next(r for r in list_res.data["resultados"] if r["id"] == mov.id)
        self.assertIsNone(item["criado_por_nome"])
