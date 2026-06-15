"""E-mails transacionais do núcleo (boas-vindas, etc.)."""

from __future__ import annotations

import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from .password_reset import smtp_pronto_para_redefinicao

logger = logging.getLogger(__name__)

User = get_user_model()


def enviar_boas_vindas(*, user: User, senha_temporaria: str) -> None:
    """Envia credenciais iniciais ou nova senha temporária (não loga a senha)."""
    if not (user.email or "").strip():
        raise ValueError("Usuário sem e-mail cadastrado.")

    backend = getattr(settings, "EMAIL_BACKEND", "")
    if "smtp" in backend.lower() and not smtp_pronto_para_redefinicao():
        raise RuntimeError(
            "SMTP sem credenciais completas (EMAIL_HOST_USER / EMAIL_HOST_PASSWORD)."
        )

    login_url = f"{settings.FRONTEND_URL.rstrip('/')}/login"
    nome = (user.first_name or user.username or "").strip() or user.email
    context = {
        "nome": nome,
        "email": user.email,
        "senha_temporaria": senha_temporaria,
        "login_url": login_url,
        "debug": settings.DEBUG,
    }
    subject = "Sua conta no Gestão Artesanal"
    text_body = render_to_string("emails/boas_vindas.txt", context)
    html_body = render_to_string("emails/boas_vindas.html", context)
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=False)
