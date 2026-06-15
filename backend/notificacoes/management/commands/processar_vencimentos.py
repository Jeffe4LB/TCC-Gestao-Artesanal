"""Comando: gera notificações para títulos vencidos e a vencer.

Uso típico (cron diário, ex.: 08:00):

    0 8 * * * cd /caminho/app/backend && /caminho/venv/bin/python manage.py processar_vencimentos

Opções:
    --dias-a-vencer N   Janela de dias para o alerta "vence em breve" (default: 3)
    --hoje YYYY-MM-DD   Força a data base (útil para testes/replay)
"""

from __future__ import annotations

from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from notificacoes.notificacoes_proativas import (
    DIAS_A_VENCER,
    notificar_vencimentos_pagar,
    notificar_vencimentos_receber,
)


class Command(BaseCommand):
    help = "Gera notificações para títulos vencidos e a vencer (próximos N dias)."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--dias-a-vencer",
            type=int,
            default=DIAS_A_VENCER,
            help=f"Dias à frente para considerar 'a vencer' (default: {DIAS_A_VENCER}).",
        )
        parser.add_argument(
            "--hoje",
            type=str,
            default="",
            help="Força a data base no formato AAAA-MM-DD (default: hoje).",
        )

    def handle(self, *args, **options) -> None:
        dias = max(0, int(options["dias_a_vencer"]))
        hoje_str = (options.get("hoje") or "").strip()
        hoje = None
        if hoje_str:
            try:
                hoje = datetime.strptime(hoje_str, "%Y-%m-%d").date()
            except ValueError as exc:
                raise CommandError(f"Data base inválida: {hoje_str}. Use AAAA-MM-DD.") from exc

        totais_pagar = notificar_vencimentos_pagar(hoje=hoje, dias_a_vencer=dias)
        totais_receber = notificar_vencimentos_receber(hoje=hoje, dias_a_vencer=dias)

        criadas_total = (
            totais_pagar["vencidas_criadas"]
            + totais_pagar["a_vencer_criadas"]
            + totais_receber["vencidas_criadas"]
            + totais_receber["a_vencer_criadas"]
        )

        self.stdout.write(self.style.SUCCESS("Processamento de vencimentos concluído."))
        self.stdout.write(
            f"  Contas a pagar:    {totais_pagar['vencidas_criadas']} vencidas, "
            f"{totais_pagar['a_vencer_criadas']} a vencer."
        )
        self.stdout.write(
            f"  Contas a receber:  {totais_receber['vencidas_criadas']} vencidas, "
            f"{totais_receber['a_vencer_criadas']} a vencer."
        )
        self.stdout.write(f"  Notificações novas: {criadas_total}")
