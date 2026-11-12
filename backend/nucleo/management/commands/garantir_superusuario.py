"""Garante a existência e atualização do superusuário a partir de variáveis de ambiente."""

from __future__ import annotations

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from nucleo.models import PerfilUsuario


class Command(BaseCommand):
    help = (
        "Cria ou atualiza o superusuário definido por DJANGO_SUPERUSER_USERNAME, "
        "DJANGO_SUPERUSER_EMAIL e DJANGO_SUPERUSER_PASSWORD."
    )

    def handle(self, *args, **options):
        username = (os.getenv("DJANGO_SUPERUSER_USERNAME") or "admin").strip()
        password = (os.getenv("DJANGO_SUPERUSER_PASSWORD") or "").strip()
        email = (
            os.getenv("DJANGO_SUPERUSER_EMAIL") or "admin@gestaoartesanal.local"
        ).strip()

        if not username or not password:
            self.stdout.write(
                self.style.WARNING(
                    "[garantir_superusuario] DJANGO_SUPERUSER_PASSWORD não definida; ignorando."
                )
            )
            return

        User = get_user_model()
        with transaction.atomic():
            user = User.objects.filter(username__iexact=username).first()
            created = False
            if user is None:
                user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password,
                )
                created = True
            else:
                user.username = username
                if email and not User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
                    user.email = email
                user.is_staff = True
                user.is_superuser = True
                user.is_active = True
                user.set_password(password)
                user.save()

            PerfilUsuario.objects.update_or_create(
                usuario=user,
                defaults={
                    "papel": PerfilUsuario.Papel.ADMIN,
                    "senha_temporaria": False,
                },
            )

        acao = "criado" if created else "atualizado"
        self.stdout.write(
            self.style.SUCCESS(
                f"[garantir_superusuario] Superusuário '{user.username}' (id={user.pk}) {acao} com sucesso."
            )
        )
