"""Configuração de produção.

Estende `config.settings` e aperta os parafusos de segurança:

- `DEBUG=False` obrigatório (raise se ficar em True).
- HTTPS forçado, HSTS de 1 ano, cookies `Secure`+`HttpOnly`.
- Cabeçalhos `X-Content-Type-Options`, `Referrer-Policy`, `X-Frame-Options`.
- CSP mais estrita (sem `'unsafe-eval'`).
- `ALLOWED_HOSTS` obrigatório (raise se vazio).
- `SESSION_COOKIE_SAMESITE = "Lax"` (CSRF) e tempo de sessão reduzido.

Ative com:

    DJANGO_SETTINGS_MODULE=config.settings_prod gunicorn config.wsgi:application

Antes do primeiro deploy, rode `python manage.py check --deploy` com este
módulo carregado para confirmar zero warnings críticos.
"""

from __future__ import annotations

import os

from .settings import *  # noqa: F401,F403
from .settings import REST_FRAMEWORK  # re-import explícito para mutate

# ---------------------------------------------------------------------------
# Hardening básico
# ---------------------------------------------------------------------------

DEBUG = False

# ALLOWED_HOSTS obrigatório em produção.
ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv("ALLOWED_HOSTS", "").split(",")
    if h.strip()
]
if not ALLOWED_HOSTS:
    raise RuntimeError(
        "ALLOWED_HOSTS vazio em produção. Defina os domínios reais no .env "
        "(ex.: ALLOWED_HOSTS=app.gestao-artesanal.com.br,api.gestao-artesanal.com.br)."
    )


# ---------------------------------------------------------------------------
# HTTPS + HSTS
# ---------------------------------------------------------------------------

# Comum: app atrás de proxy (nginx, Cloudflare) que termina TLS.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# HSTS — começar com valor baixo e aumentar gradualmente é uma boa prática.
# Default 1 ano com preload, mas configurável por env para deploys iniciais.
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))  # 1 ano
SECURE_HSTS_INCLUDE_SUBDOMAINS = (
    os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "1").lower() in ("1", "true", "yes")
)
SECURE_HSTS_PRELOAD = (
    os.getenv("SECURE_HSTS_PRELOAD", "1").lower() in ("1", "true", "yes")
)


# ---------------------------------------------------------------------------
# Browser hardening
# ---------------------------------------------------------------------------

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# Cookies: SameSite + HttpOnly + Secure (já acima).
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # precisa ser legível pelo JS para enviar no header X-CSRFToken
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# Tempo de sessão (admin Django) — 12h é suficiente. JWT (API) tem TTL próprio.
SESSION_COOKIE_AGE = int(os.getenv("SESSION_COOKIE_AGE", str(60 * 60 * 12)))


# ---------------------------------------------------------------------------
# Throttling mais agressivo em produção
# ---------------------------------------------------------------------------

REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    "anon": os.getenv("THROTTLE_RATE_ANON", "30/min"),
    "user": os.getenv("THROTTLE_RATE_USER", "120/min"),
    "login": os.getenv("THROTTLE_RATE_LOGIN", "5/min"),
    "register": os.getenv("THROTTLE_RATE_REGISTER", "10/hour"),
    "password_reset": os.getenv("THROTTLE_RATE_PASSWORD_RESET", "3/hour"),
}


# ---------------------------------------------------------------------------
# CSP estrita (sem `'unsafe-eval'`; mantém `'unsafe-inline'` em style por
# causa do Ant Design)
# ---------------------------------------------------------------------------

CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": ["'self'"],
        "script-src": ["'self'"],
        "style-src": ["'self'", "'unsafe-inline'"],
        "img-src": ["'self'", "data:", "blob:"],
        "font-src": ["'self'", "data:"],
        "connect-src": ["'self'"],
        "frame-ancestors": ["'none'"],
        "base-uri": ["'self'"],
        "form-action": ["'self'"],
        "object-src": ["'none'"],
        "upgrade-insecure-requests": [],
    },
}
