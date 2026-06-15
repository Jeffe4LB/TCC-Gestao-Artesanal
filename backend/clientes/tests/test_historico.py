from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from clientes.models import Cliente
from financeiro.models import ContaReceber
from nucleo.models import PerfilUsuario

User = get_user_model()


class ClienteHistoricoFinanceiroTests(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(
            nome="Cliente Hist",
            documento="",
            telefone="",
            email="",
        )
        ContaReceber.objects.create(
            cliente=self.cliente,
            descricao="Venda A",
            valor=Decimal("100.00"),
            vencimento=date(2026, 5, 10),
            situacao=ContaReceber.Situacao.ABERTO,
        )
        ContaReceber.objects.create(
            cliente=self.cliente,
            descricao="Venda B",
            valor=Decimal("250.00"),
            vencimento=date(2026, 4, 1),
            recebido_em=date(2026, 4, 5),
            situacao=ContaReceber.Situacao.RECEBIDO,
        )
        self.api = APIClient()
        self.user_fin = User.objects.create_user(username="fin", password="x")
        perfil = self.user_fin.perfil_usuario
        perfil.papel = PerfilUsuario.Papel.COLABORADOR
        perfil.colaborador_financeiro = True
        perfil.save()
        self.api.force_authenticate(user=self.user_fin)

    def test_historico_retorna_titulos_e_resumo(self):
        url = f"/api/v1/clientes/{self.cliente.pk}/historico-financeiro/"
        response = self.api.get(url)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total"], 2)
        self.assertEqual(len(body["resultados"]), 2)
        self.assertEqual(body["resumo"]["aberto"], "100.00")
        self.assertEqual(body["resumo"]["recebido"], "250.00")
        self.assertEqual(body["resumo"]["cancelado"], "0.00")
        descricoes = {item["descricao"] for item in body["resultados"]}
        self.assertEqual(descricoes, {"Venda A", "Venda B"})

    def test_sem_capacidade_financeiro_retorna_403(self):
        user = User.objects.create_user(username="sem_fin", password="x")
        perfil = user.perfil_usuario
        perfil.papel = PerfilUsuario.Papel.COLABORADOR
        perfil.colaborador_dados_mestres = True
        perfil.colaborador_financeiro = False
        perfil.save()
        client = APIClient()
        client.force_authenticate(user=user)
        url = f"/api/v1/clientes/{self.cliente.pk}/historico-financeiro/"
        response = client.get(url)
        self.assertEqual(response.status_code, 403)
