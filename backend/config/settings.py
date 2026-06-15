"""Configuração de desenvolvimento.

Para deploy use `DJANGO_SETTINGS_MODULE=config.settings_prod`, que estende
este arquivo e aperta os parafusos de segurança (HTTPS, HSTS, CSP, cookies).
"""

from __future__ import annotations

import hashlib
import os
import secrets
import sys
from datetime import timedelta
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

load_dotenv()

# Certificados raiz (ex.: Gmail SMTP no macOS com Python.org sem bundle).
try:
    import certifi

    _CERTIFI_CA = certifi.where()
    os.environ.setdefault("SSL_CERT_FILE", _CERTIFI_CA)
except ImportError:
    _CERTIFI_CA = None

BASE_DIR = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Segredos
# ---------------------------------------------------------------------------

DEBUG = os.getenv("DEBUG", "True").lower() in ("1", "true", "yes")

_MGMT_SAFE_COMMANDS = {
    "test",
    "makemigrations",
    "migrate",
    "showmigrations",
    "collectstatic",
    "check",
    "shell",
    "createsuperuser",
    "loaddata",
    "dumpdata",
    "listar_usuarios_auth",
}


def _resolver_secret_key() -> str:
    """Lê `SECRET_KEY` do ambiente.

    Em produção (`DEBUG=False` e comando real de servidor), exige a variável.
    Em comandos de manutenção (`migrate`, `test`, `makemigrations`, ...) gera
    uma chave efêmera para não bloquear o fluxo. Em desenvolvimento (`DEBUG=True`)
    sem chave configurada, gera uma chave efêmera com aviso no stderr.
    """
    chave = os.getenv("SECRET_KEY", "").strip()
    if chave:
        return chave

    comando = sys.argv[1] if len(sys.argv) > 1 else ""

    if comando in _MGMT_SAFE_COMMANDS:
        return "dev-management-command-" + secrets.token_urlsafe(16)

    if DEBUG:
        print(
            "[settings] AVISO: SECRET_KEY não definida; usando chave efêmera (DEBUG=True).",
            file=sys.stderr,
        )
        return "dev-fallback-" + secrets.token_urlsafe(32)

    raise RuntimeError(
        "SECRET_KEY não definida. Configure no backend/.env antes de iniciar o "
        "servidor em produção. Gere uma com: "
        "python -c \"import secrets; print(secrets.token_urlsafe(64))\""
    )


SECRET_KEY = _resolver_secret_key()


# SimpleJWT / PyJWT: HS256 recomenda chave >= 32 bytes (evita InsecureKeyLengthWarning).
_jwt_signing_key_env = os.getenv("JWT_SIGNING_KEY", "").strip()
if _jwt_signing_key_env:
    JWT_SIGNING_KEY = _jwt_signing_key_env
elif len(SECRET_KEY.encode("utf-8")) >= 32:
    JWT_SIGNING_KEY = SECRET_KEY
else:
    JWT_SIGNING_KEY = hashlib.sha256(SECRET_KEY.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Hosts permitidos
# ---------------------------------------------------------------------------

ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    if h.strip()
]
if DEBUG and "testserver" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append("testserver")


# ---------------------------------------------------------------------------
# Apps / Middleware
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_filters",
    "csp",
    "nucleo",
    "produtos",
    "clientes",
    "estoque",
    "financeiro",
    "relatorios",
    "notificacoes",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # CSP — gera o cabeçalho Content-Security-Policy.
    "csp.middleware.CSPMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# ---------------------------------------------------------------------------
# Banco de dados (apenas PostgreSQL)
# ---------------------------------------------------------------------------

_database_url = os.getenv("DATABASE_URL", "").strip()
if _database_url:
    DATABASES = {
        "default": dj_database_url.config(
            default=_database_url,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME", "gestao_artesanal"),
            "USER": os.getenv("DB_USER", "postgres"),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", "127.0.0.1"),
            "PORT": os.getenv("DB_PORT", "5432"),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ---------------------------------------------------------------------------
# Cache (relatórios read-only — TTL curto)
# ---------------------------------------------------------------------------

RELATORIO_CACHE_TTL = int(os.getenv("RELATORIO_CACHE_TTL", "60"))

_redis_url = os.getenv("REDIS_URL", "").strip()
if _redis_url:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": _redis_url,
            "TIMEOUT": RELATORIO_CACHE_TTL,
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "gestart-cache",
            "TIMEOUT": RELATORIO_CACHE_TTL,
        }
    }


# ---------------------------------------------------------------------------
# DRF + Throttling
# ---------------------------------------------------------------------------

# Limites globais. `anon`/`user` aplicam-se a todas as views via
# `DEFAULT_THROTTLE_CLASSES`. `ScopedRateThrottle` ativa-se apenas em views que
# declaram `throttle_scope` (ex.: login, register, password_reset).
#
# Em testes (`manage.py test`) o throttling fica em valores muito altos para
# não interferir com a suíte. Para validar throttle especificamente, os testes
# correspondentes usam `override_settings` e zeram o cache do throttle.

THROTTLE_RATE_ANON = os.getenv("THROTTLE_RATE_ANON", "60/min")
THROTTLE_RATE_USER = os.getenv("THROTTLE_RATE_USER", "300/min")
THROTTLE_RATE_LOGIN = os.getenv("THROTTLE_RATE_LOGIN", "10/min")
THROTTLE_RATE_REGISTER = os.getenv("THROTTLE_RATE_REGISTER", "20/hour")
THROTTLE_RATE_PASSWORD_RESET = os.getenv("THROTTLE_RATE_PASSWORD_RESET", "5/hour")

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "nucleo.pagination.PaginacaoPortugues",
    "PAGE_SIZE": 20,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": THROTTLE_RATE_ANON,
        "user": THROTTLE_RATE_USER,
        "login": THROTTLE_RATE_LOGIN,
        "register": THROTTLE_RATE_REGISTER,
        "password_reset": THROTTLE_RATE_PASSWORD_RESET,
    },
}

# Em testes automatizados, afrouxamos os limites globais para não dar 429
# falso-positivo entre testes da mesma classe.
if "test" in sys.argv:
    REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
        "anon": "1000/min",
        "user": "10000/min",
        "login": "1000/min",
        "register": "1000/min",
        "password_reset": "1000/min",
    }


SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "SIGNING_KEY": JWT_SIGNING_KEY,
}


# ---------------------------------------------------------------------------
# CORS / CSRF
# ---------------------------------------------------------------------------

CORS_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://127.0.0.1:5173,http://localhost:5173",
    ).split(",")
    if o.strip()
]
CORS_ALLOW_CREDENTIALS = True

# Domínios confiáveis para POST/PATCH/DELETE com proteção CSRF (admin Django).
CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CSRF_TRUSTED_ORIGINS",
        ",".join(CORS_ALLOWED_ORIGINS),
    ).split(",")
    if o.strip()
]


# ---------------------------------------------------------------------------
# E-mail / SPA
# ---------------------------------------------------------------------------

# Link nos e-mails de recuperação de senha (SPA)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:5173")

DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@gestao-artesanal.local")
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "").strip()
# Senhas de app do Google vêm com espaços na tela; o SMTP exige 16 caracteres contínuos.
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "").replace(" ", "").strip()
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "1").lower() in ("1", "true", "yes")
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "0").lower() in ("1", "true", "yes")
# Não definir EMAIL_SSL_CERTFILE com certifi.where(): esse setting é certificado de
# cliente SMTP, não bundle de CAs. A verificação TLS usa SSL_CERT_FILE (acima).

# Recuperação de senha (token opaco em banco; ver nucleo.password_reset)
PASSWORD_RESET_TOKEN_TTL = int(os.getenv("PASSWORD_RESET_TOKEN_TTL", "3600"))
PASSWORD_RESET_RATE_LIMIT_IP = int(os.getenv("PASSWORD_RESET_RATE_LIMIT_IP", "20"))
PASSWORD_RESET_RATE_LIMIT_EMAIL = int(os.getenv("PASSWORD_RESET_RATE_LIMIT_EMAIL", "5"))
PASSWORD_RESET_RATE_LIMIT_WINDOW = int(os.getenv("PASSWORD_RESET_RATE_LIMIT_WINDOW", "3600"))


# ---------------------------------------------------------------------------
# Content Security Policy (django-csp 4.x)
# ---------------------------------------------------------------------------

# Política base bem permissiva para desenvolvimento — em `settings_prod` a
# política é endurecida. `'unsafe-inline'` em `style-src` é necessário porque
# Ant Design injeta `<style>` inline para temas/animações.
CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": ["'self'"],
        "script-src": ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
        "style-src": ["'self'", "'unsafe-inline'"],
        "img-src": ["'self'", "data:", "blob:"],
        "font-src": ["'self'", "data:"],
        "connect-src": ["'self'", "ws://127.0.0.1:5173", "ws://localhost:5173"],
        "frame-ancestors": ["'none'"],
        "base-uri": ["'self'"],
        "form-action": ["'self'"],
    },
}
