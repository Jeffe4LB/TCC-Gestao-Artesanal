"""Testes da camada de notificações proativas (signal de estoque + services)."""

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

from estoque.models import MovimentacaoEstoque, SaldoEstoque
from estoque.services import aplicar_movimentacao
from financeiro.models import ContaPagar, ContaReceber
from notificacoes.models import NotificacaoUsuario
from notificacoes.notificacoes_proativas import (
    criar_notificacao,
    notificar_vencimentos_pagar,
    notificar_vencimentos_receber,
    usuarios_destinatarios,
)
from notificacoes.services import contar_notificacoes_nao_lidas
from produtos.models import Categoria, Fornecedor, Produto

User = get_user_model()


def _criar_admin(username: str = "admin@test.com", email: str | None = None):
    """Superuser tem todas as capacidades; serve como destinatário padrão."""
    return User.objects.create_superuser(
        username=username,
        password="Passw0rd!",
        email=email or username,
    )


def _criar_produto(*, sku: str = "P-001", minimo: Decimal | str = "10") -> Produto:
    cat = Categoria.objects.create(nome="Categoria Teste")
    forn = Fornecedor.objects.create(nome="Forn")
    return Produto.objects.create(
        sku=sku,
        nome=f"Produto {sku}",
        categoria=cat,
        fornecedor=forn,
        unidade="UN",
        preco_venda=Decimal("10.00"),
        custo_aquisicao=Decimal("4"),
        custo_unitario=Decimal("4"),
        estoque_minimo=Decimal(minimo),
    )


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class SignalEstoqueMinimoTests(TestCase):
    def setUp(self):
        self.admin = _criar_admin("admin1@test.com")
        self.produto = _criar_produto(sku="ABC-1", minimo="10")
        # saldo inicial > mínimo
        SaldoEstoque.objects.filter(produto=self.produto).update(quantidade=Decimal("20"))

    def _mover(self, delta: Decimal | str) -> None:
        """Aplica movimentação e executa os callbacks `on_commit` (signal).

        `TestCase` faz rollback ao final do teste, então `transaction.on_commit`
        nunca dispara naturalmente. `captureOnCommitCallbacks(execute=True)`
        força a execução para validar o signal.
        """
        with self.captureOnCommitCallbacks(execute=True):
            aplicar_movimentacao(
                product=self.produto,
                quantity_delta=Decimal(delta),
                movement_type=MovimentacaoEstoque.TipoMovimentacao.AJUSTE,
            )

    def test_movimento_que_derruba_saldo_abaixo_minimo_cria_notificacao(self):
        self._mover("-15")  # 20 - 15 = 5 (abaixo do mínimo 10)
        notif = NotificacaoUsuario.objects.filter(
            usuario=self.admin,
            tipo=NotificacaoUsuario.Tipo.ESTOQUE_MINIMO,
            referencia_id=self.produto.pk,
            lida_em__isnull=True,
        )
        self.assertEqual(notif.count(), 1)
        self.assertEqual(notif.first().nivel, NotificacaoUsuario.Nivel.CRITICO)

    def test_movimento_acima_minimo_nao_cria_notificacao(self):
        self._mover("-5")  # 20 - 5 = 15 (acima do mínimo)
        self.assertEqual(
            NotificacaoUsuario.objects.filter(
                tipo=NotificacaoUsuario.Tipo.ESTOQUE_MINIMO
            ).count(),
            0,
        )

    def test_dois_movimentos_no_mesmo_dia_nao_duplicam(self):
        self._mover("-15")
        self._mover("-1")  # ainda abaixo do mínimo
        self.assertEqual(
            NotificacaoUsuario.objects.filter(
                tipo=NotificacaoUsuario.Tipo.ESTOQUE_MINIMO,
                referencia_id=self.produto.pk,
            ).count(),
            1,
        )

    def test_saldo_volta_acima_do_minimo_resolve_notificacao(self):
        self._mover("-15")
        self.assertEqual(
            NotificacaoUsuario.objects.filter(
                tipo=NotificacaoUsuario.Tipo.ESTOQUE_MINIMO,
                referencia_id=self.produto.pk,
                lida_em__isnull=True,
            ).count(),
            1,
        )
        self._mover("20")  # 5 + 20 = 25 (acima do mínimo)
        self.assertEqual(
            NotificacaoUsuario.objects.filter(
                tipo=NotificacaoUsuario.Tipo.ESTOQUE_MINIMO,
                referencia_id=self.produto.pk,
                lida_em__isnull=True,
            ).count(),
            0,
        )

    def test_envia_email_para_destinatarios(self):
        self.admin.email = "admin_email@test.com"
        self.admin.save(update_fields=["email"])
        self._mover("-15")
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertIn(self.produto.sku, msg.subject)
        self.assertIn(self.produto.sku, msg.body)
        # corpo HTML alternativo presente
        self.assertTrue(any("html" in t for _, t in msg.alternatives))


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class CriarNotificacaoComDedupTests(TestCase):
    def setUp(self):
        self.user = _criar_admin("dedup@test.com")

    def test_segunda_chamada_com_mesma_chave_nao_duplica(self):
        ref = date(2026, 1, 15)
        n1 = criar_notificacao(
            usuario=self.user,
            tipo=NotificacaoUsuario.Tipo.TITULO_VENCIDO,
            titulo="x",
            mensagem="y",
            referencia_app="financeiro",
            referencia_id=42,
            data_referencia=ref,
        )
        n2 = criar_notificacao(
            usuario=self.user,
            tipo=NotificacaoUsuario.Tipo.TITULO_VENCIDO,
            titulo="x",
            mensagem="y",
            referencia_app="financeiro",
            referencia_id=42,
            data_referencia=ref,
        )
        self.assertIsNotNone(n1)
        self.assertIsNone(n2)
        self.assertEqual(
            NotificacaoUsuario.objects.filter(referencia_id=42).count(), 1
        )

    def test_chave_diferente_quando_usuario_difere(self):
        outro = _criar_admin("dedup2@test.com")
        ref = date(2026, 1, 15)
        for u in (self.user, outro):
            criar_notificacao(
                usuario=u,
                tipo=NotificacaoUsuario.Tipo.TITULO_VENCIDO,
                titulo="x",
                mensagem="y",
                referencia_app="financeiro",
                referencia_id=42,
                data_referencia=ref,
            )
        self.assertEqual(
            NotificacaoUsuario.objects.filter(referencia_id=42).count(), 2
        )

    def test_destinatarios_padrao_inclui_superuser(self):
        destinatarios = usuarios_destinatarios(NotificacaoUsuario.Tipo.ESTOQUE_MINIMO)
        self.assertIn(self.user, destinatarios)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class NotificarVencimentosTests(TestCase):
    def setUp(self):
        self.admin = _criar_admin("fin@test.com", email="fin@test.com")
        self.hoje = date(2026, 6, 15)

    def test_cria_notificacao_para_vencidas(self):
        cp = ContaPagar.objects.create(
            descricao="Aluguel",
            valor=Decimal("500"),
            vencimento=self.hoje - timedelta(days=2),
            situacao=ContaPagar.Situacao.ABERTO,
        )
        totais = notificar_vencimentos_pagar(hoje=self.hoje)
        self.assertEqual(totais["vencidas_criadas"], 1)
        self.assertEqual(totais["a_vencer_criadas"], 0)
        n = NotificacaoUsuario.objects.get(
            tipo=NotificacaoUsuario.Tipo.TITULO_VENCIDO, referencia_id=cp.pk
        )
        self.assertEqual(n.nivel, NotificacaoUsuario.Nivel.CRITICO)

    def test_cria_notificacao_para_a_vencer(self):
        cp = ContaPagar.objects.create(
            descricao="Internet",
            valor=Decimal("100"),
            vencimento=self.hoje + timedelta(days=2),
            situacao=ContaPagar.Situacao.ABERTO,
        )
        totais = notificar_vencimentos_pagar(hoje=self.hoje)
        self.assertEqual(totais["a_vencer_criadas"], 1)
        n = NotificacaoUsuario.objects.get(
            tipo=NotificacaoUsuario.Tipo.TITULO_A_VENCER, referencia_id=cp.pk
        )
        self.assertEqual(n.nivel, NotificacaoUsuario.Nivel.AVISO)

    def test_ignora_paga_e_cancelada(self):
        ContaPagar.objects.create(
            descricao="Paga",
            valor=Decimal("10"),
            vencimento=self.hoje - timedelta(days=5),
            situacao=ContaPagar.Situacao.PAGO,
        )
        ContaPagar.objects.create(
            descricao="Cancelada",
            valor=Decimal("10"),
            vencimento=self.hoje - timedelta(days=5),
            situacao=ContaPagar.Situacao.CANCELADO,
        )
        totais = notificar_vencimentos_pagar(hoje=self.hoje)
        self.assertEqual(totais["vencidas_criadas"], 0)

    def test_segunda_execucao_no_mesmo_dia_nao_duplica(self):
        ContaPagar.objects.create(
            descricao="Aluguel",
            valor=Decimal("500"),
            vencimento=self.hoje - timedelta(days=1),
            situacao=ContaPagar.Situacao.ABERTO,
        )
        notificar_vencimentos_pagar(hoje=self.hoje)
        totais2 = notificar_vencimentos_pagar(hoje=self.hoje)
        self.assertEqual(totais2["vencidas_criadas"], 0)
        self.assertEqual(
            NotificacaoUsuario.objects.filter(
                tipo=NotificacaoUsuario.Tipo.TITULO_VENCIDO
            ).count(),
            1,
        )

    def test_envia_email_para_vencidas_mas_nao_para_a_vencer(self):
        ContaPagar.objects.create(
            descricao="Vencida",
            valor=Decimal("50"),
            vencimento=self.hoje - timedelta(days=1),
            situacao=ContaPagar.Situacao.ABERTO,
        )
        ContaPagar.objects.create(
            descricao="A vencer",
            valor=Decimal("50"),
            vencimento=self.hoje + timedelta(days=2),
            situacao=ContaPagar.Situacao.ABERTO,
        )
        notificar_vencimentos_pagar(hoje=self.hoje)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("venceu", mail.outbox[0].subject.lower())

    def test_receber_funciona_analogamente(self):
        from clientes.models import Cliente

        cli = Cliente.objects.create(nome="C", documento="", telefone="", email="")
        ContaReceber.objects.create(
            cliente=cli,
            descricao="Pedido",
            data_emissao=self.hoje - timedelta(days=10),
            valor=Decimal("100"),
            vencimento=self.hoje - timedelta(days=3),
            situacao=ContaReceber.Situacao.ABERTO,
        )
        totais = notificar_vencimentos_receber(hoje=self.hoje)
        self.assertEqual(totais["vencidas_criadas"], 1)


class ResumoNotificacoesNaoLidasTests(TestCase):
    def setUp(self):
        self.user = _criar_admin("resumo@test.com")

    def test_resumo_inclui_contagem_nao_lidas(self):
        NotificacaoUsuario.objects.create(
            usuario=self.user,
            tipo=NotificacaoUsuario.Tipo.ESTOQUE_MINIMO,
            titulo="A",
        )
        NotificacaoUsuario.objects.create(
            usuario=self.user,
            tipo=NotificacaoUsuario.Tipo.TITULO_VENCIDO,
            titulo="B",
        )
        NotificacaoUsuario.objects.create(
            usuario=self.user,
            tipo=NotificacaoUsuario.Tipo.TITULO_VENCIDO,
            titulo="C",
            lida_em=timezone.now(),
        )
        resumo = contar_notificacoes_nao_lidas(self.user)
        self.assertEqual(resumo["total"], 2)
        self.assertEqual(resumo["por_tipo"]["estoque_minimo"], 1)
        self.assertEqual(resumo["por_tipo"]["titulo_vencido"], 1)
