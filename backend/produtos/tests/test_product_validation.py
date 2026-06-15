from decimal import Decimal

from django.test import TestCase

from produtos.models import Categoria, Fornecedor, Produto
from produtos.serializers import ProdutoSerializer


class ProductSerializerValidationTests(TestCase):
    def setUp(self):
        self.cat = Categoria.objects.create(nome="Cat")
        self.sup = Fornecedor.objects.create(nome="S")

    def test_purchased_accepts_zero_sale_price(self):
        ser = ProdutoSerializer(
            data={
                "sku": "P-ZS",
                "nome": "P",
                "categoria": self.cat.pk,
                "tipo_produto": "comprado",
                "unidade": "UN",
                "preco_venda": "0",
                "custo_aquisicao": "5.00",
                "estoque_minimo": "0",
                "ativo": True,
            }
        )
        self.assertTrue(ser.is_valid(), ser.errors)
        obj = ser.save()
        self.assertEqual(obj.preco_venda, Decimal("0.00"))

    def test_manufactured_rejects_zero_sale_price(self):
        ser = ProdutoSerializer(
            data={
                "sku": "M-ZS",
                "nome": "Fab",
                "categoria": self.cat.pk,
                "tipo_produto": "fabricado",
                "unidade": "UN",
                "preco_venda": "0",
                "custo_aquisicao": "0",
                "estoque_minimo": "0",
                "ativo": True,
            }
        )
        self.assertFalse(ser.is_valid())
        self.assertIn("preco_venda", ser.errors)

    def test_purchased_rejects_zero_purchase_cost(self):
        ser = ProdutoSerializer(
            data={
                "sku": "P-ZC",
                "nome": "P",
                "categoria": self.cat.pk,
                "tipo_produto": "comprado",
                "unidade": "UN",
                "preco_venda": "10.00",
                "custo_aquisicao": "0",
                "estoque_minimo": "0",
                "ativo": True,
            }
        )
        self.assertFalse(ser.is_valid())
        self.assertIn("custo_aquisicao", ser.errors)

    def test_purchased_accepts_positive_values(self):
        ser = ProdutoSerializer(
            data={
                "sku": "P-OK",
                "nome": "P",
                "categoria": self.cat.pk,
                "tipo_produto": "comprado",
                "unidade": "UN",
                "preco_venda": "10.00",
                "custo_aquisicao": "3.50",
                "estoque_minimo": "0",
                "ativo": True,
            }
        )
        self.assertTrue(ser.is_valid(), ser.errors)

    def test_manufactured_accepts_zero_purchase_cost(self):
        ser = ProdutoSerializer(
            data={
                "sku": "M-1",
                "nome": "Fab",
                "categoria": self.cat.pk,
                "tipo_produto": "fabricado",
                "unidade": "UN",
                "preco_venda": "12.00",
                "custo_aquisicao": "0",
                "estoque_minimo": "0",
                "ativo": True,
            }
        )
        self.assertTrue(ser.is_valid(), ser.errors)

    def test_blank_unit_rejected(self):
        ser = ProdutoSerializer(
            data={
                "sku": "U-X",
                "nome": "P",
                "categoria": self.cat.pk,
                "tipo_produto": "comprado",
                "unidade": "   ",
                "preco_venda": "1.00",
                "custo_aquisicao": "1.00",
                "estoque_minimo": "0",
                "ativo": True,
            }
        )
        self.assertFalse(ser.is_valid())
        self.assertIn("unidade", ser.errors)

    def test_update_purchased_requires_positive_cost_in_payload(self):
        p = Produto.objects.create(
            sku="PATCH-1",
            nome="X",
            categoria=self.cat,
            tipo_produto=Produto.TipoProduto.COMPRADO,
            unidade="UN",
            preco_venda=Decimal("10.00"),
            custo_aquisicao=Decimal("2.00"),
        )
        ser = ProdutoSerializer(
            p,
            data={
                "custo_aquisicao": "0",
            },
            partial=True,
        )
        self.assertFalse(ser.is_valid())
        self.assertIn("custo_aquisicao", ser.errors)
