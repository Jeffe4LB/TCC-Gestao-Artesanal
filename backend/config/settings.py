import hashlib
from datetime import timedelta
from pathlib import Path

import os
from dotenv import load_dotenv

load_dotenv()

# Certificados raiz (ex.: Gmail SMTP no macOS com Python.org sem bundle).
try:
    import certifi

    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me-in-env")
DEBUG = os.getenv("DEBUG", "True").lower() in ("1", "true", "yes")

# SimpleJWT / PyJWT: HS256 recomenda chave >= 32 bytes (evita InsecureKeyLengthWarning).
_jwt_signing_key_env = os.getenv("JWT_SIGNING_KEY", "").strip()
if _jwt_signing_key_env:
    JWT_SIGNING_KEY = _jwt_signing_key_env
elif len(SECRET_KEY.encode("utf-8")) >= 32:
    JWT_SIGNING_KEY = SECRET_KEY
else:
    JWT_SIGNING_KEY = hashlib.sha256(SECRET_KEY.encode("utf-8")).hexdigest()

ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    if h.strip()
]
if DEBUG and "testserver" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append("testserver")

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
    "core",
    "products",
    "customers",
    "stock",
    "finance",
    "reports",
    "notifications",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
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

# Apenas PostgreSQL — defina DB_* no `.env` (ver `.env.example`).
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

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

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
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "SIGNING_KEY": JWT_SIGNING_KEY,
}

CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
]

CORS_ALLOW_CREDENTIALS = True

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

# Recuperação de senha (token opaco em banco; ver core.password_reset)
PASSWORD_RESET_TOKEN_TTL = int(os.getenv("PASSWORD_RESET_TOKEN_TTL", "3600"))
PASSWORD_RESET_RATE_LIMIT_IP = int(os.getenv("PASSWORD_RESET_RATE_LIMIT_IP", "20"))
PASSWORD_RESET_RATE_LIMIT_EMAIL = int(os.getenv("PASSWORD_RESET_RATE_LIMIT_EMAIL", "5"))
PASSWORD_RESET_RATE_LIMIT_WINDOW = int(os.getenv("PASSWORD_RESET_RATE_LIMIT_WINDOW", "3600"))
