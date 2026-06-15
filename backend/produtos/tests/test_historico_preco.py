from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from nucleo.models import PerfilUsuario
from produtos.models import Categoria, Fornecedor, HistoricoPreco, Produto

User = get_user_model()


class HistoricoPrecoTests(TestCase):
    def setUp(self):
        self.cat = Categoria.objects.create(nome="Cat")
        self.forn = Fornecedor.objects.create(nome="Forn")
        self.user = User.objects.create_user(username="dados", password="x")
        perfil = self.user.perfil_usuario
        perfil.papel = PerfilUsuario.Papel.COLABORADOR
        perfil.colaborador_dados_mestres = True
        perfil.save()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_alteracao_preco_cria_historico(self):
        produto = Produto.objects.create(
            sku="HIST-1",
            nome="Histórico",
            categoria=self.cat,
            fornecedor=self.forn,
            preco_venda=Decimal("10.00"),
            custo_aquisicao=Decimal("5.00"),
            custo_unitario=Decimal("5.00"),
        )
        produto.preco_venda = Decimal("12.00")
        produto.save()
        self.assertEqual(HistoricoPreco.objects.filter(produto=produto).count(), 1)
        reg = HistoricoPreco.objects.get(produto=produto)
        self.assertEqual(reg.preco_venda_anterior, Decimal("10.00"))
        self.assertEqual(reg.preco_venda_novo, Decimal("12.00"))

    def test_endpoint_historico_precos(self):
        produto = Produto.objects.create(
            sku="HIST-2",
            nome="API",
            categoria=self.cat,
            fornecedor=self.forn,
            preco_venda=Decimal("1.00"),
            custo_unitario=Decimal("1.00"),
        )
        produto.preco_venda = Decimal("2.00")
        produto.save()
        response = self.client.get(f"/api/v1/produtos/{produto.pk}/historico-precos/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
