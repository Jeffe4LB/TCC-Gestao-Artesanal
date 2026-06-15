"""Teste do management command `processar_vencimentos`."""

from datetime import date, timedelta
from decimal import Decimal
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from clientes.models import Cliente
from financeiro.models import ContaPagar, ContaReceber
from notificacoes.models import NotificacaoUsuario

User = get_user_model()


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class ProcessarVencimentosCommandTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="cmd@test.com", password="x", email="cmd@test.com"
        )
        self.hoje = date(2026, 6, 15)

    def _criar_contas(self):
        ContaPagar.objects.create(
            descricao="Vencida",
            valor=Decimal("50"),
            vencimento=self.hoje - timedelta(days=2),
            situacao=ContaPagar.Situacao.ABERTO,
        )
        ContaPagar.objects.create(
            descricao="A vencer",
            valor=Decimal("60"),
            vencimento=self.hoje + timedelta(days=2),
            situacao=ContaPagar.Situacao.ABERTO,
        )
        cli = Cliente.objects.create(nome="X", documento="", telefone="", email="")
        ContaReceber.objects.create(
            cliente=cli,
            descricao="R-1",
            data_emissao=self.hoje - timedelta(days=10),
            valor=Decimal("70"),
            vencimento=self.hoje - timedelta(days=1),
            situacao=ContaReceber.Situacao.ABERTO,
        )

    def test_comando_cria_notificacoes_para_todas_as_contas(self):
        self._criar_contas()
        out = StringIO()
        call_command("processar_vencimentos", f"--hoje={self.hoje.isoformat()}", stdout=out)
        saida = out.getvalue()
        self.assertIn("Processamento de vencimentos concluído", saida)
        # 2 contas a pagar (1 vencida + 1 a vencer) + 1 a receber vencida = 3
        self.assertEqual(NotificacaoUsuario.objects.filter(usuario=self.admin).count(), 3)

    def test_comando_idempotente_no_mesmo_dia(self):
        self._criar_contas()
        call_command("processar_vencimentos", f"--hoje={self.hoje.isoformat()}", stdout=StringIO())
        call_command("processar_vencimentos", f"--hoje={self.hoje.isoformat()}", stdout=StringIO())
        # mesmo número de notificações após 2 execuções
        self.assertEqual(NotificacaoUsuario.objects.filter(usuario=self.admin).count(), 3)

    def test_data_invalida_levanta_erro(self):
        with self.assertRaises(CommandError):
            call_command("processar_vencimentos", "--hoje=2026-99-99", stdout=StringIO())

    def test_dias_a_vencer_zero_ignora_proximos(self):
        # somente vencidos serão notificados quando dias-a-vencer=0
        ContaPagar.objects.create(
            descricao="V",
            valor=Decimal("10"),
            vencimento=self.hoje - timedelta(days=3),
            situacao=ContaPagar.Situacao.ABERTO,
        )
        ContaPagar.objects.create(
            descricao="A",
            valor=Decimal("10"),
            vencimento=self.hoje + timedelta(days=10),
            situacao=ContaPagar.Situacao.ABERTO,
        )
        call_command(
            "processar_vencimentos",
            f"--hoje={self.hoje.isoformat()}",
            "--dias-a-vencer=0",
            stdout=StringIO(),
        )
        # Só a vencida virou notificação
        self.assertEqual(
            NotificacaoUsuario.objects.filter(
                tipo=NotificacaoUsuario.Tipo.TITULO_VENCIDO
            ).count(),
            1,
        )
        self.assertEqual(
            NotificacaoUsuario.objects.filter(
                tipo=NotificacaoUsuario.Tipo.TITULO_A_VENCER
            ).count(),
            0,
        )
