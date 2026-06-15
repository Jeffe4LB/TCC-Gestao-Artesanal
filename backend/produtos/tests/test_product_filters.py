from django.test import TestCase

from produtos.filters import FiltroProduto
from produtos.models import Categoria, Produto


class FiltroProdutoTests(TestCase):
    def setUp(self):
        self.cat = Categoria.objects.create(nome="Cat")
        self.comprado = Produto.objects.create(
            sku="C-1",
            nome="Comprado",
            categoria=self.cat,
            tipo_produto=Produto.TipoProduto.COMPRADO,
            unidade="UN",
        )
        self.fabricado = Produto.objects.create(
            sku="F-1",
            nome="Fabricado",
            categoria=self.cat,
            tipo_produto=Produto.TipoProduto.FABRICADO,
            unidade="UN",
        )

    def test_filter_tipo_produto_api_fabricado(self):
        qs = Produto.objects.all()
        f = FiltroProduto({"tipo_produto": "fabricado"}, queryset=qs)
        self.assertTrue(f.is_valid(), f.errors)
        ids = list(f.qs.values_list("pk", flat=True))
        self.assertEqual(ids, [self.fabricado.pk])

    def test_filter_tipo_produto_api_comprado(self):
        qs = Produto.objects.all()
        f = FiltroProduto({"tipo_produto": "comprado"}, queryset=qs)
        self.assertTrue(f.is_valid(), f.errors)
        ids = list(f.qs.values_list("pk", flat=True))
        self.assertEqual(ids, [self.comprado.pk])
