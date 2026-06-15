"""Tokens de redefinição de senha (uso único, expiração) e envio de e-mail."""

from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from .models import TokenRedefinicaoSenha

logger = logging.getLogger(__name__)

User = get_user_model()


def _token_ttl_seconds() -> int:
    return int(getattr(settings, "PASSWORD_RESET_TOKEN_TTL", 3600))


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def get_client_ip(request) -> str:
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()[:45]
    return (request.META.get("REMOTE_ADDR") or "unknown")[:45]


def rate_limit_allows(request, email_normalized: str) -> bool:
    """Retorna False se exceder limites (não enviar e-mail)."""
    ip = get_client_ip(request)
    ip_key = f"pwdreset:ip:{ip}"
    email_key = f"pwdreset:email:{email_normalized}"
    ip_max = int(getattr(settings, "PASSWORD_RESET_RATE_LIMIT_IP", 20))
    email_max = int(getattr(settings, "PASSWORD_RESET_RATE_LIMIT_EMAIL", 5))
    window = int(getattr(settings, "PASSWORD_RESET_RATE_LIMIT_WINDOW", 3600))

    def count_up(key: str) -> int:
        n = cache.get(key)
        if n is None:
            cache.set(key, 1, window)
            return 1
        try:
            return cache.incr(key)
        except ValueError:
            cache.set(key, 1, window)
            return 1

    if cache.get(ip_key, 0) >= ip_max or cache.get(email_key, 0) >= email_max:
        return False
    count_up(ip_key)
    count_up(email_key)
    return True


def emitir_token_para_usuario(user: User) -> str:
    """Remove pendentes válidos, cria novo token e devolve o valor em texto claro (só para o e-mail)."""
    now = timezone.now()
    TokenRedefinicaoSenha.objects.filter(
        usuario=user, usado_em__isnull=True, expira_em__gt=now
    ).delete()
    raw = secrets.token_urlsafe(32)
    TokenRedefinicaoSenha.objects.create(
        usuario=user,
        hash_token=hash_token(raw),
        expira_em=now + timedelta(seconds=_token_ttl_seconds()),
    )
    return raw


def build_reset_url(uid_b64: str, raw_token: str) -> str:
    base = settings.FRONTEND_URL.rstrip("/")
    return f"{base}/redefinir-senha?uid={uid_b64}&token={raw_token}"


def send_password_reset_email(*, user: User, raw_token: str) -> None:
    uid_b64 = urlsafe_base64_encode(force_bytes(user.pk))
    reset_url = build_reset_url(uid_b64, raw_token)
    ttl = _token_ttl_seconds()
    hours = max(1, (ttl + 3599) // 3600)
    subject = "Redefinição de senha — Gestão Artesanal"
    context = {
        "reset_url": reset_url,
        "expires_hours": hours,
        "username": user.username,
        "debug": settings.DEBUG,
    }
    text_body = (
        "Você solicitou redefinir a senha da sua conta.\n\n"
        f"Acesse o link (válido por cerca de {hours} hora(s)):\n{reset_url}\n\n"
    )
    if settings.DEBUG:
        text_body += (
            "Desenvolvimento: o link usa FRONTEND_URL (ex.: http://127.0.0.1:5173). "
            "Antes de clicar, inicie o front com: npm run dev (porta 5173). "
            "Se abrir o e-mail no celular, 127.0.0.1 aponta para o próprio aparelho — use o PC ou ajuste FRONTEND_URL para o IP da sua máquina na rede.\n\n"
        )
    text_body += "Se você não fez este pedido, ignore este e-mail."
    html_body = render_to_string("emails/redefinicao_senha.html", context)
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=False)


def encontrar_usuario_por_uid_b64(uid_b64: str) -> User | None:
    try:
        uid = force_str(urlsafe_base64_decode(uid_b64))
        return User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        return None


def consumir_token(user: User, raw_token: str) -> bool:
    """
    Marca token como usado se válido. Retorna True se havia token válido.
    A senha deve ser alterada pelo caller após True.
    """
    now = timezone.now()
    h = hash_token(raw_token)
    row = (
        TokenRedefinicaoSenha.objects.filter(
            usuario=user,
            hash_token=h,
            usado_em__isnull=True,
            expira_em__gt=now,
        )
        .order_by("-criado_em")
        .first()
    )
    if not row:
        return False
    row.usado_em = now
    row.save(update_fields=["usado_em"])
    return True


def _smtp_missing_credentials() -> bool:
    backend = getattr(settings, "EMAIL_BACKEND", "")
    if "smtp" not in backend.lower():
        return False
    user = (getattr(settings, "EMAIL_HOST_USER", None) or "").strip()
    password = (getattr(settings, "EMAIL_HOST_PASSWORD", None) or "").strip()
    return not user or not password


def smtp_pronto_para_redefinicao() -> bool:
    """False quando o backend está em SMTP mas faltam credenciais (e-mail de reset não será enviado)."""
    return not _smtp_missing_credentials()


def tentar_enviar_emails_redefinicao(request, email_normalized: str) -> None:
    users = list(User.objects.filter(email__iexact=email_normalized).exclude(email=""))
    if not users:
        return
    if _smtp_missing_credentials():
        logger.error(
            "password_reset: SMTP sem EMAIL_HOST_PASSWORD. Defina no .env a senha de app (16 caracteres, sem espaços)."
        )
        return
    if not rate_limit_allows(request, email_normalized):
        logger.warning(
            "password_reset rate limited email=%s ip=%s",
            email_normalized,
            get_client_ip(request),
        )
        return
    for user in users:
        raw = emitir_token_para_usuario(user)
        try:
            send_password_reset_email(user=user, raw_token=raw)
        except Exception:
            logger.exception(
                "password_reset email failed user_id=%s to=%s",
                user.pk,
                user.email,
            )


# Aliases legados
issue_token_for_user = emitir_token_para_usuario
find_user_from_uid_b64 = encontrar_usuario_por_uid_b64
consume_token = consumir_token
try_send_reset_emails = tentar_enviar_emails_redefinicao
smtp_ready_for_password_reset = smtp_pronto_para_redefinicao
