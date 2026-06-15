from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient

from estoque.models import MovimentacaoEstoque, SaldoEstoque
from estoque.services import cancelar_ordem_producao, executar_producao
from nucleo.models import PerfilUsuario
from produtos.models import Categoria, Fornecedor, Produto

User = get_user_model()


def _usuario_producao():
    user = User.objects.create_user(username="api_prod", password="x")
    perfil = user.perfil_usuario
    perfil.papel = PerfilUsuario.Papel.COLABORADOR
    perfil.colaborador_receitas_producao = True
    perfil.save()
    return user


class CancelamentoProducaoServiceTests(TestCase):
    def setUp(self):
        self.cat = Categoria.objects.create(nome="Cat")
        self.sup = Fornecedor.objects.create(nome="Forn")
        self.insumo = Produto.objects.create(
            sku="INS-1",
            nome="Insumo",
            categoria=self.cat,
            fornecedor=self.sup,
            tipo_produto=Produto.TipoProduto.COMPRADO,
            unidade="UN",
            preco_venda=Decimal("10"),
            custo_aquisicao=Decimal("5"),
            custo_unitario=Decimal("5"),
        )
        self.fabricado = Produto.objects.create(
            sku="FAB-1",
            nome="Fabricado",
            categoria=self.cat,
            fornecedor=self.sup,
            tipo_produto=Produto.TipoProduto.FABRICADO,
            unidade="UN",
            preco_venda=Decimal("50"),
            custo_aquisicao=Decimal("0"),
            custo_unitario=Decimal("10"),
        )
        SaldoEstoque.objects.update_or_create(
            produto=self.insumo,
            defaults={"quantidade": Decimal("100")},
        )
        SaldoEstoque.objects.update_or_create(
            produto=self.fabricado,
            defaults={"quantidade": Decimal("0")},
        )
        self.user = User.objects.create_user(username="prod", password="x")

    def _executar_ordem(self):
        return executar_producao(
            produto_id=self.fabricado.pk,
            quantity_produced="10",
            lines=[{"component": self.insumo.pk, "quantity_consumed": "2"}],
            user=self.user,
        )

    def test_cancelar_restaura_saldos(self):
        saldo_insumo_antes = SaldoEstoque.objects.get(produto=self.insumo).quantidade
        saldo_fab_antes = SaldoEstoque.objects.get(produto=self.fabricado).quantidade

        ordem = self._executar_ordem()
        self.assertEqual(
            SaldoEstoque.objects.get(produto=self.insumo).quantidade,
            saldo_insumo_antes - Decimal("2"),
        )
        self.assertEqual(
            SaldoEstoque.objects.get(produto=self.fabricado).quantidade,
            saldo_fab_antes + Decimal("10"),
        )

        cancelar_ordem_producao(ordem=ordem, user=self.user)

        self.assertEqual(
            SaldoEstoque.objects.get(produto=self.insumo).quantidade,
            saldo_insumo_antes,
        )
        self.assertEqual(
            SaldoEstoque.objects.get(produto=self.fabricado).quantidade,
            saldo_fab_antes,
        )

    def test_cancelar_marca_ordem_e_movimentos_originais(self):
        ordem = self._executar_ordem()
        cancelar_ordem_producao(ordem=ordem, user=self.user)

        ordem.refresh_from_db()
        self.assertIsNotNone(ordem.cancelada_em)
        self.assertEqual(ordem.cancelada_por_id, self.user.pk)
        self.assertFalse(ordem.ativa)

        originais = MovimentacaoEstoque.objects.filter(
            ordem_producao=ordem,
            tipo_movimentacao__in=[
                MovimentacaoEstoque.TipoMovimentacao.ENTRADA_PRODUCAO,
                MovimentacaoEstoque.TipoMovimentacao.CONSUMO_PRODUCAO,
            ],
        )
        self.assertEqual(originais.count(), 2)
        self.assertTrue(all(m.producao_substituta for m in originais))

    def test_cancelar_cria_movimentos_estorno(self):
        ordem = self._executar_ordem()
        cancelar_ordem_producao(ordem=ordem, user=self.user)

        estornos = MovimentacaoEstoque.objects.filter(
            ordem_producao=ordem,
            tipo_movimentacao__in=[
                MovimentacaoEstoque.TipoMovimentacao.ESTORNO_ENTRADA_PRODUCAO,
                MovimentacaoEstoque.TipoMovimentacao.ESTORNO_CONSUMO_PRODUCAO,
            ],
            producao_substituta=False,
        )
        self.assertEqual(estornos.count(), 2)

    def test_cancelar_duplo_falha(self):
        ordem = self._executar_ordem()
        cancelar_ordem_producao(ordem=ordem, user=self.user)
        with self.assertRaises(ValidationError) as ctx:
            cancelar_ordem_producao(ordem=ordem, user=self.user)
        self.assertIn("já foi cancelada", str(ctx.exception))

    def test_cancelar_sem_estoque_acabado_falha(self):
        ordem = self._executar_ordem()
        saldo_fab = SaldoEstoque.objects.select_for_update().get(produto=self.fabricado)
        saldo_fab.quantidade = Decimal("0")
        saldo_fab.save(update_fields=["quantidade"])

        with self.assertRaises(ValidationError) as ctx:
            cancelar_ordem_producao(ordem=ordem, user=self.user)
        self.assertIn("Estoque insuficiente", str(ctx.exception))
        ordem.refresh_from_db()
        self.assertIsNone(ordem.cancelada_em)


class CancelamentoProducaoApiTests(TestCase):
    def setUp(self):
        self.cat = Categoria.objects.create(nome="Cat")
        self.sup = Fornecedor.objects.create(nome="Forn")
        self.insumo = Produto.objects.create(
            sku="INS-API",
            nome="Insumo API",
            categoria=self.cat,
            fornecedor=self.sup,
            tipo_produto=Produto.TipoProduto.COMPRADO,
            unidade="UN",
            preco_venda=Decimal("10"),
            custo_aquisicao=Decimal("5"),
            custo_unitario=Decimal("5"),
        )
        self.fabricado = Produto.objects.create(
            sku="FAB-API",
            nome="Fabricado API",
            categoria=self.cat,
            fornecedor=self.sup,
            tipo_produto=Produto.TipoProduto.FABRICADO,
            unidade="UN",
            preco_venda=Decimal("50"),
            custo_aquisicao=Decimal("0"),
            custo_unitario=Decimal("10"),
        )
        SaldoEstoque.objects.update_or_create(
            produto=self.insumo,
            defaults={"quantidade": Decimal("100")},
        )
        SaldoEstoque.objects.update_or_create(
            produto=self.fabricado,
            defaults={"quantidade": Decimal("0")},
        )
        self.user = _usuario_producao()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def _criar_ordem_via_api(self):
        res = self.client.post(
            "/api/v1/ordens-producao/",
            {
                "produto": self.fabricado.pk,
                "quantidade_produzida": "5",
                "linhas": [
                    {
                        "insumo": self.insumo.pk,
                        "quantidade_consumida": "1",
                    }
                ],
            },
            format="json",
        )
        self.assertEqual(res.status_code, 201, res.data)
        return res.data["id"]

    def test_api_cancelar_com_jwt(self):
        ordem_id = self._criar_ordem_via_api()
        res = self.client.post(f"/api/v1/ordens-producao/{ordem_id}/cancelar/")
        self.assertEqual(res.status_code, 200, res.data)
        self.assertIsNotNone(res.data["cancelada_em"])
        self.assertEqual(res.data["cancelada_por"], self.user.pk)
        self.assertFalse(res.data["ativa"])

    def test_api_cancelar_duplo_retorna_400(self):
        ordem_id = self._criar_ordem_via_api()
        self.assertEqual(
            self.client.post(f"/api/v1/ordens-producao/{ordem_id}/cancelar/").status_code,
            200,
        )
        res = self.client.post(f"/api/v1/ordens-producao/{ordem_id}/cancelar/")
        self.assertEqual(res.status_code, 400, res.data)

    def test_api_cancelar_sem_capacidade_retorna_403(self):
        ordem_id = self._criar_ordem_via_api()
        sem_cap = User.objects.create_user(username="sem_prod", password="x")
        perfil = sem_cap.perfil_usuario
        perfil.papel = PerfilUsuario.Papel.COLABORADOR
        perfil.colaborador_receitas_producao = False
        perfil.save()
        client = APIClient()
        client.force_authenticate(user=sem_cap)
        res = client.post(f"/api/v1/ordens-producao/{ordem_id}/cancelar/")
        self.assertEqual(res.status_code, 403)

    def test_api_lista_filtro_ativa(self):
        ordem_id = self._criar_ordem_via_api()
        ativas = self.client.get("/api/v1/ordens-producao/?ativa=true")
        self.assertEqual(ativas.status_code, 200)
        ids_ativas = {r["id"] for r in ativas.data["resultados"]}
        self.assertIn(ordem_id, ids_ativas)

        self.client.post(f"/api/v1/ordens-producao/{ordem_id}/cancelar/")

        ativas_depois = self.client.get("/api/v1/ordens-producao/?ativa=true")
        ids_ativas_depois = {r["id"] for r in ativas_depois.data["resultados"]}
        self.assertNotIn(ordem_id, ids_ativas_depois)

        canceladas = self.client.get("/api/v1/ordens-producao/?ativa=false")
        ids_canceladas = {r["id"] for r in canceladas.data["resultados"]}
        self.assertIn(ordem_id, ids_canceladas)
