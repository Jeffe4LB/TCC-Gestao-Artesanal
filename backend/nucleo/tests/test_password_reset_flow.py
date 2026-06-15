from datetime import timedelta

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from nucleo.models import TokenRedefinicaoSenha
from nucleo.password_reset import hash_token, issue_token_for_user


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    PASSWORD_RESET_RATE_LIMIT_IP=1000,
    PASSWORD_RESET_RATE_LIMIT_EMAIL=1000,
    FRONTEND_URL="http://test-frontend.example",
    DEFAULT_FROM_EMAIL="sender@example.com",
)
class PasswordResetApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="OldPasswd1!",
        )

    def test_forgot_sends_email_with_link(self):
        mail.outbox.clear()
        r = self.client.post("/api/v1/auth/password/reset/", {"email": "alice@example.com"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertIn(self.user.email, msg.to)
        self.assertIn("/redefinir-senha", msg.body)
        self.assertTrue(TokenRedefinicaoSenha.objects.filter(usuario=self.user).exists())

    def test_confirm_resets_password_single_use(self):
        raw = issue_token_for_user(self.user)
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        r1 = self.client.post(
            "/api/v1/auth/password/reset/confirm/",
            {
                "uid": uid,
                "token": raw,
                "new_password": "NewPasswd2!",
                "new_password_confirm": "NewPasswd2!",
            },
            format="json",
        )
        self.assertEqual(r1.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPasswd2!"))
        r2 = self.client.post(
            "/api/v1/auth/password/reset/confirm/",
            {
                "uid": uid,
                "token": raw,
                "new_password": "OtherPass3!",
                "new_password_confirm": "OtherPass3!",
            },
            format="json",
        )
        self.assertEqual(r2.status_code, 400)
        self.assertIn("já utilizado", r2.json().get("detail", ""))

    def test_expired_token_rejected(self):
        raw = "x" * 20
        TokenRedefinicaoSenha.objects.create(
            usuario=self.user,
            hash_token=hash_token(raw),
            expira_em=timezone.now() - timedelta(hours=1),
        )
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        r = self.client.post(
            "/api/v1/auth/password/reset/confirm/",
            {
                "uid": uid,
                "token": raw,
                "new_password": "NewPasswd2!",
                "new_password_confirm": "NewPasswd2!",
            },
            format="json",
        )
        self.assertEqual(r.status_code, 400)

    def test_forgot_alias_path(self):
        mail.outbox.clear()
        r = self.client.post("/api/v1/auth/password/forgot/", {"email": "alice@example.com"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
