from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient

from clientes.models import Cliente
from financeiro.models import ContaPagar, DocumentoFinanceiro
from financeiro.services import (
    cancelar_documento,
    criar_documento_com_parcelas,
    quitar_parcela,
)
from produtos.models import Fornecedor


class ParcelamentoServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="fin", password="Fin12345!")
        self.fornecedor = Fornecedor.objects.create(nome="Fornecedor X")
        self.cliente = Cliente.objects.create(nome="Cliente Y", documento="", telefone="", email="")

    def test_documento_3_parcelas_soma_bate_com_valor_total(self):
        doc = criar_documento_com_parcelas(
            tipo="pagar",
            valor_total=Decimal("100.00"),
            numero_parcelas=3,
            primeira_data=date(2026, 6, 1),
            intervalo_dias=30,
            descricao="Compra parcelada",
            fornecedor=self.fornecedor,
            usuario=self.user,
        )
        parcelas = list(doc.contas_pagar.order_by("numero_parcela"))
        self.assertEqual(len(parcelas), 3)
        self.assertEqual(parcelas[0].valor, Decimal("33.33"))
        self.assertEqual(parcelas[1].valor, Decimal("33.33"))
        self.assertEqual(parcelas[2].valor, Decimal("33.34"))
        self.assertEqual(sum(p.valor for p in parcelas), Decimal("100.00"))
        self.assertEqual(doc.valor_total, Decimal("100.00"))
        self.assertEqual(doc.numero_parcelas, 3)
        self.assertEqual(parcelas[0].vencimento, date(2026, 6, 1))
        self.assertEqual(parcelas[1].vencimento, date(2026, 7, 1))
        self.assertEqual(parcelas[2].vencimento, date(2026, 7, 31))

    def test_documento_receber_cria_parcelas(self):
        doc = criar_documento_com_parcelas(
            tipo="receber",
            valor_total=Decimal("50.00"),
            numero_parcelas=2,
            primeira_data=date(2026, 5, 10),
            intervalo_dias=15,
            descricao="Venda parcelada",
            cliente=self.cliente,
            usuario=self.user,
        )
        self.assertEqual(doc.tipo, DocumentoFinanceiro.Tipo.RECEBER)
        parcelas = list(doc.contas_receber.order_by("numero_parcela"))
        self.assertEqual(len(parcelas), 2)
        self.assertEqual(sum(p.valor for p in parcelas), Decimal("50.00"))

    def test_baixa_parcial_muda_status_para_parcial(self):
        doc = criar_documento_com_parcelas(
            tipo="pagar",
            valor_total=Decimal("100.00"),
            numero_parcelas=1,
            primeira_data=date.today(),
            fornecedor=self.fornecedor,
        )
        parcela = doc.contas_pagar.get()
        quitar_parcela(
            parcela=parcela,
            valor_pago=Decimal("40.00"),
            data_pagamento=date.today(),
        )
        parcela.refresh_from_db()
        self.assertEqual(parcela.situacao, ContaPagar.Situacao.PARCIAL)
        self.assertEqual(parcela.valor_pago, Decimal("40.00"))
        self.assertIsNone(parcela.pago_em)
        doc.refresh_from_db()
        self.assertEqual(doc.situacao, DocumentoFinanceiro.Situacao.ABERTO)

    def test_baixa_completa_quita_documento(self):
        doc = criar_documento_com_parcelas(
            tipo="pagar",
            valor_total=Decimal("60.00"),
            numero_parcelas=2,
            primeira_data=date.today(),
            fornecedor=self.fornecedor,
        )
        for parcela in doc.contas_pagar.order_by("numero_parcela"):
            quitar_parcela(
                parcela=parcela,
                valor_pago=parcela.valor,
                data_pagamento=date.today(),
            )
        doc.refresh_from_db()
        self.assertEqual(doc.situacao, DocumentoFinanceiro.Situacao.QUITADO)
        self.assertTrue(
            all(p.situacao == ContaPagar.Situacao.PAGO for p in doc.contas_pagar.all())
        )

    def test_baixa_excedente_rejeita(self):
        doc = criar_documento_com_parcelas(
            tipo="pagar",
            valor_total=Decimal("10.00"),
            numero_parcelas=1,
            primeira_data=date.today(),
            fornecedor=self.fornecedor,
        )
        parcela = doc.contas_pagar.get()
        with self.assertRaises(ValidationError):
            quitar_parcela(
                parcela=parcela,
                valor_pago=Decimal("15.00"),
                data_pagamento=date.today(),
            )

    def test_cancelar_documento_cancela_parcelas_em_aberto(self):
        doc = criar_documento_com_parcelas(
            tipo="pagar",
            valor_total=Decimal("90.00"),
            numero_parcelas=3,
            primeira_data=date.today(),
            fornecedor=self.fornecedor,
        )
        parcelas = list(doc.contas_pagar.order_by("numero_parcela"))
        quitar_parcela(
            parcela=parcelas[0],
            valor_pago=parcelas[0].valor,
            data_pagamento=date.today(),
        )
        cancelar_documento(doc)
        doc.refresh_from_db()
        self.assertEqual(doc.situacao, DocumentoFinanceiro.Situacao.CANCELADO)
        parcelas[0].refresh_from_db()
        parcelas[1].refresh_from_db()
        parcelas[2].refresh_from_db()
        self.assertEqual(parcelas[0].situacao, ContaPagar.Situacao.PAGO)
        self.assertEqual(parcelas[1].situacao, ContaPagar.Situacao.CANCELADO)
        self.assertEqual(parcelas[2].situacao, ContaPagar.Situacao.CANCELADO)


class DocumentoFinanceiroApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username="admin", password="Admin12345!", email="a@a.com")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.fornecedor = Fornecedor.objects.create(nome="F API")
        self.cliente = Cliente.objects.create(nome="C API", documento="", telefone="", email="")

    def test_post_documentos_financeiros_cria_parcelas(self):
        res = self.client.post(
            "/api/v1/documentos-financeiros/",
            {
                "tipo": "pagar",
                "fornecedor": self.fornecedor.pk,
                "descricao": "Doc API",
                "valor_total": "120.00",
                "numero_parcelas": 4,
                "primeira_data": "2026-07-01",
                "intervalo_dias": 30,
                "observacoes": "",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 201, res.content)
        self.assertEqual(len(res.data["parcelas"]), 4)
        self.assertEqual(res.data["tipo"], "pagar")
        self.assertEqual(res.data["valor_total"], "120.00")

    def test_cancelar_documento_via_api(self):
        criado = self.client.post(
            "/api/v1/documentos-financeiros/",
            {
                "tipo": "receber",
                "cliente": self.cliente.pk,
                "descricao": "Cancelar",
                "valor_total": "30.00",
                "numero_parcelas": 1,
                "primeira_data": "2026-07-01",
            },
            format="json",
        ).data
        res = self.client.post(f"/api/v1/documentos-financeiros/{criado['id']}/cancelar/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["situacao"], "cancelado")

    def test_quitar_parcela_via_api(self):
        criado = self.client.post(
            "/api/v1/documentos-financeiros/",
            {
                "tipo": "pagar",
                "fornecedor": self.fornecedor.pk,
                "descricao": "Quitar",
                "valor_total": "25.00",
                "numero_parcelas": 1,
                "primeira_data": "2026-07-01",
            },
            format="json",
        ).data
        parcela_id = criado["parcelas"][0]["id"]
        res = self.client.post(
            f"/api/v1/documentos-financeiros/{criado['id']}/quitar-parcela/",
            {
                "parcela_id": parcela_id,
                "valor": "10.00",
                "data_pagamento": "2026-07-05",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        parcela = res.data["parcelas"][0]
        self.assertEqual(parcela["situacao"], "parcial")
        self.assertEqual(str(parcela["valor_pago"]), "10.00")
