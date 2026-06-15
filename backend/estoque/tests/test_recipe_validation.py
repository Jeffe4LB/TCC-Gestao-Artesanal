from decimal import Decimal

from django.test import TestCase

from estoque.serializers import ReceitaSerializer
from produtos.costs import finalizar_custo_unitario_produto
from produtos.models import Categoria, Fornecedor, Produto


class RecipeSerializerBomCostValidationTests(TestCase):
    def setUp(self):
        self.cat = Categoria.objects.create(nome="Mat")
        self.sup = Fornecedor.objects.create(nome="F")
        self.comp = Produto.objects.create(
            sku="INS-R",
            nome="Insumo",
            categoria=self.cat,
            fornecedor=self.sup,
            tipo_produto=Produto.TipoProduto.COMPRADO,
            unidade="KG",
            preco_venda=Decimal("1.00"),
            custo_aquisicao=Decimal("5.00"),
        )
        finalizar_custo_unitario_produto(self.comp)
        self.fab = Produto.objects.create(
            sku="FAB-R",
            nome="Acabado",
            categoria=self.cat,
            tipo_produto=Produto.TipoProduto.FABRICADO,
            unidade="UN",
            preco_venda=Decimal("20.00"),
            custo_aquisicao=Decimal("0"),
        )

    def test_accepts_recipe_with_zero_bom_cost(self):
        """Permite salvar receita mesmo com custo zero (cadastro em andamento)."""
        Produto.objects.filter(pk=self.comp.pk).update(custo_unitario=Decimal("0"))
        self.comp.refresh_from_db()
        ser = ReceitaSerializer(
            data={
                "produto": self.fab.pk,
                "observacoes": "",
                "linhas": [{"insumo": self.comp.pk, "quantidade_por_unidade": "1"}],
            }
        )
        self.assertTrue(ser.is_valid(), ser.errors)
        recipe = ser.save()
        self.assertIsNotNone(recipe.pk)

    def test_accepts_positive_bom_cost(self):
        ser = ReceitaSerializer(
            data={
                "produto": self.fab.pk,
                "observacoes": "",
                "linhas": [{"insumo": self.comp.pk, "quantidade_por_unidade": "0.1"}],
            }
        )
        self.assertTrue(ser.is_valid(), ser.errors)
        recipe = ser.save()
        self.assertIsNotNone(recipe.pk)
