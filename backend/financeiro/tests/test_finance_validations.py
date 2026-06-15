from django.test import TestCase

from clientes.models import Cliente
from financeiro.serializers import ContaPagarSerializer, ContaReceberSerializer
from produtos.models import Categoria, Fornecedor, Produto


class AccountPayableAmountValidationTests(TestCase):
    def test_amount_must_be_positive(self):
        ser = ContaPagarSerializer(
            data={
                "descricao": "Conta",
                "valor": "0",
                "vencimento": "2026-04-20",
                "situacao": "aberto",
                "observacoes": "",
            }
        )
        self.assertFalse(ser.is_valid())
        self.assertIn("valor", ser.errors)


class AccountReceivableLinePriceValidationTests(TestCase):
    def setUp(self):
        from decimal import Decimal

        self.cliente = Cliente.objects.create(nome="C", documento="", telefone="", email="")
        self.cat = Categoria.objects.create(nome="G")
        self.sup = Fornecedor.objects.create(nome="S")
        self.product = Produto.objects.create(
            sku="PR-VAL",
            nome="P",
            categoria=self.cat,
            fornecedor=self.sup,
            unidade="UN",
            preco_venda=Decimal("10.00"),
            custo_aquisicao=Decimal("3.00"),
        )

    def test_unit_price_zero_invalid(self):
        ser = ContaReceberSerializer(
            data={
                "cliente": self.cliente.pk,
                "descricao": "Doc",
                "data_emissao": "2026-04-01",
                "vencimento": "2026-04-15",
                "situacao": "aberto",
                "observacoes": "",
                "linhas": [
                    {
                        "produto": self.product.pk,
                        "quantidade": "1",
                        "unidade": "UN",
                        "preco_unitario": "0",
                        "desconto": "0",
                    },
                ],
            }
        )
        self.assertFalse(ser.is_valid())
        self.assertIn("linhas", ser.errors)
