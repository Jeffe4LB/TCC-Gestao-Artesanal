"""Smoke tests dos parafusos de segurança da Fase 4.

Cobre:

- Carregamento e overrides de `config.settings_prod`.
- Throttle de login (HTTP 429 após N tentativas).
- Throttle de redefinição de senha.
- Cabeçalho `Content-Security-Policy` emitido pelo django-csp.

Detalhe sobre `ScopedRateThrottle`: o DRF avalia `THROTTLE_RATES` no momento
da importação da classe (`THROTTLE_RATES = api_settings.DEFAULT_THROTTLE_RATES`),
então `override_settings(REST_FRAMEWORK=...)` não muda os limites em tempo de
teste. Por isso, os testes que precisam reduzir o limite fazem monkey-patch
direto em `ScopedRateThrottle.THROTTLE_RATES` no `setUp` e restauram no
`tearDown`.
"""

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.throttling import ScopedRateThrottle


class SettingsProdTests(TestCase):
    """Valida os overrides em `config.settings_prod`."""

    def _reload_settings_prod(self, allowed_hosts: str = "app.exemplo.com"):
        import os
        from importlib import reload

        os.environ["ALLOWED_HOSTS"] = allowed_hosts
        try:
            from config import settings_prod

            return reload(settings_prod)
        finally:
            os.environ.pop("ALLOWED_HOSTS", None)

    def test_settings_prod_force_https_e_cookies_seguros(self):
        sp = self._reload_settings_prod()
        self.assertFalse(sp.DEBUG)
        self.assertTrue(sp.SECURE_SSL_REDIRECT)
        self.assertTrue(sp.SESSION_COOKIE_SECURE)
        self.assertTrue(sp.CSRF_COOKIE_SECURE)
        self.assertGreaterEqual(sp.SECURE_HSTS_SECONDS, 60)
        self.assertEqual(sp.X_FRAME_OPTIONS, "DENY")
        self.assertTrue(sp.SECURE_CONTENT_TYPE_NOSNIFF)
        self.assertEqual(sp.SECURE_REFERRER_POLICY, "same-origin")
        self.assertIn("app.exemplo.com", sp.ALLOWED_HOSTS)

    def test_settings_prod_csp_sem_unsafe_inline_em_script(self):
        sp = self._reload_settings_prod()
        script_src = sp.CONTENT_SECURITY_POLICY["DIRECTIVES"]["script-src"]
        self.assertNotIn("'unsafe-eval'", script_src)
        self.assertNotIn("'unsafe-inline'", script_src)
        self.assertEqual(
            sp.CONTENT_SECURITY_POLICY["DIRECTIVES"]["frame-ancestors"],
            ["'none'"],
        )

    def test_settings_prod_falha_sem_allowed_hosts(self):
        import os
        from importlib import reload

        os.environ.pop("ALLOWED_HOSTS", None)
        with self.assertRaises(RuntimeError):
            from config import settings_prod

            reload(settings_prod)


class ThrottleTestsBase(TestCase):
    """Helpers para suprimir o cache e patchar `ScopedRateThrottle.THROTTLE_RATES`."""

    def setUp(self):
        cache.clear()
        self._original_rates = dict(ScopedRateThrottle.THROTTLE_RATES)

    def tearDown(self):
        cache.clear()
        ScopedRateThrottle.THROTTLE_RATES = self._original_rates

    def _setar_rate(self, escopo: str, rate: str) -> None:
        ScopedRateThrottle.THROTTLE_RATES = {
            **ScopedRateThrottle.THROTTLE_RATES,
            escopo: rate,
        }


class ThrottleLoginTests(ThrottleTestsBase):
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        User.objects.create_user(username="bob", password="GoodPass!1")

    def test_login_bloqueia_apos_estourar_limite(self):
        self._setar_rate("login", "3/min")
        for _ in range(3):
            r = self.client.post(
                "/api/v1/auth/token/",
                {"username": "bob", "password": "wrong"},
                format="json",
            )
            self.assertIn(r.status_code, (400, 401))
        r = self.client.post(
            "/api/v1/auth/token/",
            {"username": "bob", "password": "wrong"},
            format="json",
        )
        self.assertEqual(r.status_code, 429)

    def test_login_correto_tambem_consome_quota(self):
        # 3 tentativas com senha correta — todas devolvem 200, mas a 4ª deve
        # ser barrada com 429 (defesa em profundidade contra brute force).
        self._setar_rate("login", "3/min")
        for _ in range(3):
            r = self.client.post(
                "/api/v1/auth/token/",
                {"username": "bob", "password": "GoodPass!1"},
                format="json",
            )
            self.assertEqual(r.status_code, 200, r.content)
        r = self.client.post(
            "/api/v1/auth/token/",
            {"username": "bob", "password": "GoodPass!1"},
            format="json",
        )
        self.assertEqual(r.status_code, 429)


class ThrottlePasswordResetTests(ThrottleTestsBase):
    def setUp(self):
        super().setUp()
        self.client = APIClient()

    def test_password_reset_request_bloqueia_apos_estourar(self):
        self._setar_rate("password_reset", "2/min")
        for _ in range(2):
            r = self.client.post(
                "/api/v1/auth/password/reset/",
                {"email": "x@x.com"},
                format="json",
            )
            self.assertEqual(r.status_code, 200)
        r = self.client.post(
            "/api/v1/auth/password/reset/",
            {"email": "x@x.com"},
            format="json",
        )
        self.assertEqual(r.status_code, 429)


class ThrottleRegisterTests(ThrottleTestsBase):
    def setUp(self):
        super().setUp()
        self.client = APIClient()

    def test_register_bloqueia_apos_estourar(self):
        self._setar_rate("register", "2/min")
        for i in range(2):
            r = self.client.post(
                "/api/v1/auth/register/",
                {
                    "username": f"u{i}",
                    "email": f"u{i}@x.com",
                    "password": "Senh@FortE123",
                    "first_name": "Foo",
                    "last_name": "Bar",
                },
                format="json",
            )
            self.assertIn(r.status_code, (200, 201, 400))
        r = self.client.post(
            "/api/v1/auth/register/",
            {
                "username": "outro",
                "email": "outro@x.com",
                "password": "Senh@FortE123",
                "first_name": "Foo",
                "last_name": "Bar",
            },
            format="json",
        )
        self.assertEqual(r.status_code, 429)


class CspHeaderTests(TestCase):
    """Garante que o django-csp adiciona o header em respostas."""

    def setUp(self):
        cache.clear()
        self.client = APIClient()

    def test_response_inclui_content_security_policy(self):
        r = self.client.get("/api/v1/health/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("Content-Security-Policy", r.headers)
        csp = r.headers["Content-Security-Policy"]
        self.assertIn("default-src", csp)
        self.assertIn("'self'", csp)
        self.assertIn("frame-ancestors", csp)
