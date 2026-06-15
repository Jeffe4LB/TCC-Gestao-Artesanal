from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from financeiro.models import ContaPagar
from nucleo.models import PerfilUsuario
from produtos.models import Fornecedor

User = get_user_model()


class FornecedorHistoricoFinanceiroTests(TestCase):
    def setUp(self):
        self.fornecedor = Fornecedor.objects.create(nome="Fornecedor Hist")
        ContaPagar.objects.create(
            fornecedor=self.fornecedor,
            descricao="Compra A",
            valor=Decimal("80.00"),
            vencimento=date(2026, 6, 1),
            situacao=ContaPagar.Situacao.ABERTO,
        )
        ContaPagar.objects.create(
            fornecedor=self.fornecedor,
            descricao="Compra B",
            valor=Decimal("120.00"),
            vencimento=date(2026, 3, 15),
            pago_em=date(2026, 3, 20),
            situacao=ContaPagar.Situacao.PAGO,
        )
        self.api = APIClient()
        self.user_fin = User.objects.create_user(username="fin_forn", password="x")
        perfil = self.user_fin.perfil_usuario
        perfil.papel = PerfilUsuario.Papel.COLABORADOR
        perfil.colaborador_financeiro = True
        perfil.save()
        self.api.force_authenticate(user=self.user_fin)

    def test_historico_retorna_titulos_e_resumo(self):
        url = f"/api/v1/fornecedores/{self.fornecedor.pk}/historico-financeiro/"
        response = self.api.get(url)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total"], 2)
        self.assertEqual(len(body["resultados"]), 2)
        self.assertEqual(body["resumo"]["aberto"], "80.00")
        self.assertEqual(body["resumo"]["pago"], "120.00")
        descricoes = {item["descricao"] for item in body["resultados"]}
        self.assertEqual(descricoes, {"Compra A", "Compra B"})

    def test_sem_capacidade_financeiro_retorna_403(self):
        user = User.objects.create_user(username="sem_fin_forn", password="x")
        perfil = user.perfil_usuario
        perfil.papel = PerfilUsuario.Papel.COLABORADOR
        perfil.colaborador_dados_mestres = True
        perfil.colaborador_financeiro = False
        perfil.save()
        client = APIClient()
        client.force_authenticate(user=user)
        url = f"/api/v1/fornecedores/{self.fornecedor.pk}/historico-financeiro/"
        response = client.get(url)
        self.assertEqual(response.status_code, 403)
