from decimal import Decimal

from django.db import transaction
from django.test import TestCase
from rest_framework.serializers import ValidationError as DRFValidationError

from clientes.models import Cliente
from estoque.models import MovimentacaoEstoque, SaldoEstoque
from estoque.services import reverter_movimentacoes_venda_receber_ativas
from financeiro.models import ContaReceber
from financeiro.serializers import ContaReceberSerializer
from produtos.models import Categoria, Fornecedor, Produto


class ReceivableStockIntegrationTests(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(nome="Cliente", documento="", telefone="", email="")
        self.cat = Categoria.objects.create(nome="Cat")
        self.sup = Fornecedor.objects.create(nome="Forn")
        self.product = Produto.objects.create(
            sku="EST-VENDA",
            nome="Item",
            categoria=self.cat,
            fornecedor=self.sup,
            unidade="UN",
            preco_venda=Decimal("50.00"),
            custo_aquisicao=Decimal("10.00"),
        )
        SaldoEstoque.objects.update_or_create(
            produto=self.product,
            defaults={"quantidade": Decimal("100")},
        )

    def _payload(self, *, qty: str, situacao: str = "aberto"):
        return {
            "cliente": self.cliente.pk,
            "descricao": "Fatura teste",
            "data_emissao": "2026-04-01",
            "vencimento": "2026-04-15",
            "situacao": situacao,
            "observacoes": "",
            "linhas": [
                {
                    "produto": self.product.pk,
                    "quantidade": qty,
                    "unidade": "UN",
                    "preco_unitario": "10.00",
                    "desconto": "0",
                }
            ],
        }

    def test_create_deducts_stock(self):
        ser = ContaReceberSerializer(data=self._payload(qty="7"))
        self.assertTrue(ser.is_valid(), ser.errors)
        ar = ser.save()
        bal = SaldoEstoque.objects.get(produto=self.product)
        self.assertEqual(bal.quantidade, Decimal("93"))
        self.assertEqual(
            MovimentacaoEstoque.objects.filter(
                conta_receber=ar,
                tipo_movimentacao=MovimentacaoEstoque.TipoMovimentacao.VENDA_RECEBER,
                venda_receber_substituta=False,
            ).count(),
            1,
        )

    def test_insufficient_stock_raises(self):
        ser = ContaReceberSerializer(data=self._payload(qty="150"))
        self.assertTrue(ser.is_valid(), ser.errors)
        with self.assertRaises(DRFValidationError):
            ser.save()

    def test_cancel_restores_stock(self):
        ser = ContaReceberSerializer(data=self._payload(qty="6"))
        self.assertTrue(ser.is_valid(), ser.errors)
        ar = ser.save()
        self.assertEqual(SaldoEstoque.objects.get(produto=self.product).quantidade, Decimal("94"))

        ser2 = ContaReceberSerializer(
            instance=ar, data={"situacao": "cancelado"}, partial=True
        )
        self.assertTrue(ser2.is_valid(), ser2.errors)
        ser2.save()
        self.assertEqual(SaldoEstoque.objects.get(produto=self.product).quantidade, Decimal("100"))

    def test_update_lines_rebalances_stock(self):
        ser = ContaReceberSerializer(data=self._payload(qty="2"))
        self.assertTrue(ser.is_valid(), ser.errors)
        ar = ser.save()
        self.assertEqual(SaldoEstoque.objects.get(produto=self.product).quantidade, Decimal("98"))

        ser2 = ContaReceberSerializer(
            instance=ar,
            data=self._payload(qty="20"),
        )
        self.assertTrue(ser2.is_valid(), ser2.errors)
        ser2.save()
        self.assertEqual(SaldoEstoque.objects.get(produto=self.product).quantidade, Decimal("80"))

    def test_mark_paid_does_not_double_deduct(self):
        ser = ContaReceberSerializer(data=self._payload(qty="3"))
        self.assertTrue(ser.is_valid(), ser.errors)
        ar = ser.save()
        self.assertEqual(SaldoEstoque.objects.get(produto=self.product).quantidade, Decimal("97"))

        ser2 = ContaReceberSerializer(
            instance=ar,
            data={"situacao": "recebido", "recebido_em": "2026-04-05"},
            partial=True,
        )
        self.assertTrue(ser2.is_valid(), ser2.errors)
        ser2.save()
        self.assertEqual(SaldoEstoque.objects.get(produto=self.product).quantidade, Decimal("97"))

    def test_destroy_reverts_stock(self):
        ser = ContaReceberSerializer(data=self._payload(qty="8"))
        self.assertTrue(ser.is_valid(), ser.errors)
        ar = ser.save()
        self.assertEqual(SaldoEstoque.objects.get(produto=self.product).quantidade, Decimal("92"))

        with transaction.atomic():
            reverter_movimentacoes_venda_receber_ativas(receivable=ar, user=None)
            ar.delete()

        self.assertFalse(ContaReceber.objects.filter(pk=ar.pk).exists())
        self.assertEqual(SaldoEstoque.objects.get(produto=self.product).quantidade, Decimal("100"))
