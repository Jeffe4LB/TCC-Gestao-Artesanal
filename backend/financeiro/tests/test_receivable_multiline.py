from datetime import date
from decimal import Decimal

from django.test import TestCase

from clientes.models import Cliente
from estoque.models import SaldoEstoque
from financeiro.models import ContaReceber, LinhaContaReceber
from financeiro.serializers import ContaReceberSerializer
from produtos.models import Categoria, Fornecedor, Produto


class ReceivableMultilineSerializerTests(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(nome="Cliente A", documento="", telefone="", email="")
        self.cat = Categoria.objects.create(nome="Geral")
        self.sup = Fornecedor.objects.create(nome="S")
        self.p1 = Produto.objects.create(
            sku="P1",
            nome="Produto 1",
            categoria=self.cat,
            fornecedor=self.sup,
            unidade="UN",
            preco_venda=Decimal("10.00"),
            custo_aquisicao=Decimal("5"),
            custo_unitario=Decimal("5"),
        )
        self.p2 = Produto.objects.create(
            sku="P2",
            nome="Produto 2",
            categoria=self.cat,
            fornecedor=self.sup,
            unidade="KG",
            preco_venda=Decimal("20.00"),
            custo_aquisicao=Decimal("8"),
            custo_unitario=Decimal("8"),
        )
        SaldoEstoque.objects.update_or_create(
            produto=self.p1, defaults={"quantidade": Decimal("100")}
        )
        SaldoEstoque.objects.update_or_create(
            produto=self.p2, defaults={"quantidade": Decimal("100")}
        )

    def test_create_two_lines_total_matches(self):
        ser = ContaReceberSerializer(
            data={
                "cliente": self.cliente.pk,
                "descricao": "Pedido",
                "data_emissao": "2026-04-10",
                "vencimento": "2026-04-30",
                "situacao": "aberto",
                "observacoes": "",
                "linhas": [
                    {
                        "produto": self.p1.pk,
                        "quantidade": "2",
                        "unidade": "UN",
                        "preco_unitario": "10.00",
                        "desconto": "0",
                    },
                    {
                        "produto": self.p2.pk,
                        "quantidade": "1",
                        "unidade": "KG",
                        "preco_unitario": "20.00",
                        "desconto": "0",
                    },
                ],
            }
        )
        self.assertTrue(ser.is_valid(), ser.errors)
        ar = ser.save()
        self.assertEqual(ar.valor, Decimal("40.00"))
        self.assertEqual(ar.linhas.count(), 2)

    def test_update_lines_recalculates_amount(self):
        ar = ContaReceber.objects.create(
            cliente=self.cliente,
            descricao="Doc",
            data_emissao=date(2026, 4, 1),
            valor=Decimal("0"),
            vencimento=date(2026, 4, 10),
            situacao=ContaReceber.Situacao.ABERTO,
        )
        LinhaContaReceber.objects.create(
            conta_receber=ar,
            produto=self.p1,
            quantidade=Decimal("1"),
            unidade="UN",
            preco_unitario=Decimal("10"),
            desconto=Decimal("0"),
            total_linha=Decimal("10"),
        )
        ar.valor = Decimal("10")
        ar.save()
        ser = ContaReceberSerializer(
            instance=ar,
            data={
                "cliente": self.cliente.pk,
                "descricao": "Doc",
                "data_emissao": "2026-04-01",
                "vencimento": "2026-04-10",
                "situacao": "aberto",
                "observacoes": "",
                "linhas": [
                    {
                        "produto": self.p1.pk,
                        "quantidade": "3",
                        "unidade": "UN",
                        "preco_unitario": "10.00",
                        "desconto": "0",
                    },
                ],
            },
        )
        self.assertTrue(ser.is_valid(), ser.errors)
        ar = ser.save()
        self.assertEqual(ar.valor, Decimal("30.00"))
