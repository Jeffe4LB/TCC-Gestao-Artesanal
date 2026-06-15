from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.utils import override_settings
from rest_framework.test import APIClient

from estoque.models import SaldoEstoque
from estoque.services import liberar_reserva, reservar_estoque
from nucleo.models import PerfilUsuario
from produtos.models import Categoria, Fornecedor, Produto

User = get_user_model()


def _usuario_estoque_leitura():
    user = User.objects.create_user(username="perf_est", password="x")
    perfil = user.perfil_usuario
    perfil.papel = PerfilUsuario.Papel.COLABORADOR
    perfil.colaborador_estoque_leitura = True
    perfil.save()
    return user


class AlertaEstoquePerformanceTests(TestCase):
    def setUp(self):
        self.user = _usuario_estoque_leitura()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        cat = Categoria.objects.create(nome="Cat")
        forn = Fornecedor.objects.create(nome="Forn")
        for i in range(5):
            p = Produto.objects.create(
                sku=f"LOW-{i}",
                nome=f"Prod {i}",
                categoria=cat,
                fornecedor=forn,
                unidade="UN",
                estoque_minimo=Decimal("10"),
                preco_venda=Decimal("1"),
                custo_aquisicao=Decimal("1"),
                custo_unitario=Decimal("1"),
            )
            SaldoEstoque.objects.filter(produto=p).update(quantidade=Decimal("2"))

    def test_alerta_estoque_poucas_queries_sql(self):
        with self.assertNumQueries(1):
            response = self.client.get("/api/v1/alertas-estoque/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)


class ReservaEstoqueServiceTests(TestCase):
    def setUp(self):
        cat = Categoria.objects.create(nome="C")
        forn = Fornecedor.objects.create(nome="F")
        self.produto = Produto.objects.create(
            sku="RES-1",
            nome="Reserva",
            categoria=cat,
            fornecedor=forn,
            unidade="UN",
            estoque_minimo=Decimal("0"),
            preco_venda=Decimal("1"),
            custo_aquisicao=Decimal("1"),
            custo_unitario=Decimal("1"),
        )
        SaldoEstoque.objects.filter(produto=self.produto).update(quantidade=Decimal("10"))

    def test_reservar_e_liberar_atualiza_disponivel(self):
        reservar_estoque(produto=self.produto, quantidade=Decimal("3"))
        saldo = SaldoEstoque.objects.get(produto=self.produto)
        self.assertEqual(saldo.quantidade_reservada, Decimal("3"))
        self.assertEqual(saldo.disponivel, Decimal("7"))

        liberar_reserva(produto=self.produto, quantidade=Decimal("3"))
        saldo.refresh_from_db()
        self.assertEqual(saldo.quantidade_reservada, Decimal("0"))
        self.assertEqual(saldo.disponivel, Decimal("10"))

    def test_reservar_acima_do_disponivel_falha(self):
        from django.core.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            reservar_estoque(produto=self.produto, quantidade=Decimal("20"))


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "test-cache-rel",
        }
    }
)
class CacheRelatorioTests(TestCase):
    def test_totais_financeiro_em_aberto_usa_cache(self):
        from django.core.cache import cache

        from relatorios.services import totais_financeiro_em_aberto

        cache.clear()
        primeiro = totais_financeiro_em_aberto()
        segundo = totais_financeiro_em_aberto()
        self.assertEqual(primeiro, segundo)
        self.assertIsNotNone(cache.get("rel:fin_aberto"))
