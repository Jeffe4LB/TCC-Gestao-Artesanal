from decimal import Decimal

from django.test import TestCase

from estoque.models import LinhaReceita, Receita
from produtos.costs import bom_unit_cost_sum, finalizar_custo_unitario_produto, quant_money
from produtos.models import Categoria, Fornecedor, Produto


class ManufacturedCostFromBomTests(TestCase):
    def setUp(self):
        self.cat = Categoria.objects.create(nome="Mat")
        self.sup = Fornecedor.objects.create(nome="Forn")
        self.comp = Produto.objects.create(
            sku="INS-1",
            nome="Insumo",
            categoria=self.cat,
            fornecedor=self.sup,
            tipo_produto=Produto.TipoProduto.COMPRADO,
            unidade="KG",
            preco_venda=Decimal("1.00"),
            custo_aquisicao=Decimal("10.00"),
            custo_unitario=Decimal("0"),
        )
        finalizar_custo_unitario_produto(self.comp)
        self.comp.refresh_from_db()
        self.assertEqual(self.comp.custo_unitario, Decimal("10.00"))

        self.fab = Produto.objects.create(
            sku="FAB-1",
            nome="Acabado",
            categoria=self.cat,
            tipo_produto=Produto.TipoProduto.FABRICADO,
            unidade="UN",
            preco_venda=Decimal("50.00"),
            custo_aquisicao=Decimal("0"),
            custo_unitario=Decimal("0"),
        )
        self.receita = Receita.objects.create(produto=self.fab, observacoes="")
        LinhaReceita.objects.create(
            receita=self.receita,
            insumo=self.comp,
            quantidade_por_unidade=Decimal("0.05"),
        )

    def test_bom_sum(self):
        finalizar_custo_unitario_produto(self.fab)
        self.fab.refresh_from_db()
        # 0.05 KG × R$ 10/KG = R$ 0,50
        self.assertEqual(self.fab.custo_unitario, Decimal("0.50"))

    def test_bom_unit_cost_sum_helper(self):
        self.assertEqual(bom_unit_cost_sum(self.fab), Decimal("0.50"))

    def test_component_price_change_propagates(self):
        finalizar_custo_unitario_produto(self.fab)
        self.comp.custo_aquisicao = Decimal("20.00")
        self.comp.save(update_fields=["custo_aquisicao"])
        finalizar_custo_unitario_produto(self.comp)
        self.fab.refresh_from_db()
        self.assertEqual(self.fab.custo_unitario, quant_money(Decimal("0.05") * Decimal("20.00")))
