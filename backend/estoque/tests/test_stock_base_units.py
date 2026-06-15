from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from estoque.models import MovimentacaoEstoque, SaldoEstoque
from estoque.services import aplicar_movimentacao
from nucleo.units import quantity_to_base
from produtos.costs import finalizar_custo_unitario_produto
from produtos.models import Categoria, Fornecedor, Produto


class StockMovementBaseUnitTests(TestCase):
    def setUp(self):
        self.cat = Categoria.objects.create(nome="Mat")
        self.sup = Fornecedor.objects.create(nome="F")
        self.p = Produto.objects.create(
            sku="CERA-1",
            nome="Cera",
            categoria=self.cat,
            fornecedor=self.sup,
            tipo_produto=Produto.TipoProduto.COMPRADO,
            unidade="KG",
            preco_venda=Decimal("1.00"),
            custo_aquisicao=Decimal("1.00"),
            custo_unitario=Decimal("0"),
        )
        finalizar_custo_unitario_produto(self.p)
        self.p.refresh_from_db()
        SaldoEstoque.objects.update_or_create(
            produto=self.p,
            defaults={"quantidade": Decimal("1.000")},
        )

    def test_50g_exit_reduces_kg_balance(self):
        """1 KG de saldo; saída de 50 G → restam 0,95 KG na base."""
        delta = -quantity_to_base(Decimal("50"), "G")
        aplicar_movimentacao(
            product=self.p,
            quantity_delta=delta,
            movement_type=MovimentacaoEstoque.TipoMovimentacao.AJUSTE,
            quantity_input=Decimal("50"),
            unit_input="G",
        )
        b = SaldoEstoque.objects.get(produto=self.p)
        self.assertEqual(Decimal(str(b.quantidade)), Decimal("0.950"))

    def test_insufficient_stock_raises(self):
        delta = -quantity_to_base(Decimal("2000"), "G")
        with self.assertRaises(ValidationError) as ctx:
            aplicar_movimentacao(
                product=self.p,
                quantity_delta=delta,
                movement_type=MovimentacaoEstoque.TipoMovimentacao.AJUSTE,
            )
        self.assertIn("insuficiente", str(ctx.exception).lower())
