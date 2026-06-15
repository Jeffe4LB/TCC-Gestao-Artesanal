from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from notificacoes.models import NotificacaoUsuario


class NotificacaoUsuarioApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_a = User.objects.create_user(username="a", password="Passw0rd!")
        self.user_b = User.objects.create_user(username="b", password="Passw0rd!")

    def test_list_only_own_and_unread_filter(self):
        NotificacaoUsuario.objects.create(
            usuario=self.user_a,
            nivel=NotificacaoUsuario.Nivel.INFO,
            titulo="A1",
        )
        n_unread = NotificacaoUsuario.objects.create(
            usuario=self.user_a,
            nivel=NotificacaoUsuario.Nivel.SUCESSO,
            titulo="A2",
        )
        read_n = NotificacaoUsuario.objects.create(
            usuario=self.user_a,
            nivel=NotificacaoUsuario.Nivel.AVISO,
            titulo="A3",
            lida_em=timezone.now(),
        )

        NotificacaoUsuario.objects.create(
            usuario=self.user_b,
            nivel=NotificacaoUsuario.Nivel.ERRO,
            titulo="B1",
        )

        self.client.force_authenticate(self.user_a)
        r_all = self.client.get("/api/v1/notificacoes/", format="json")
        self.assertEqual(r_all.status_code, 200)
        self.assertEqual(r_all.json()["total"], 3)

        r_unread = self.client.get("/api/v1/notificacoes/?unread=1", format="json")
        self.assertEqual(r_unread.status_code, 200)
        self.assertEqual(r_unread.json()["total"], 2)
        ids = {row["id"] for row in r_unread.json()["resultados"]}
        self.assertIn(n_unread.id, ids)
        self.assertNotIn(read_n.id, ids)

    def test_create_mark_read_mark_all(self):
        self.client.force_authenticate(self.user_a)
        c = self.client.post(
            "/api/v1/notificacoes/",
            {"nivel": "success", "titulo": "OK", "mensagem": "detalhe"},
            format="json",
        )
        self.assertEqual(c.status_code, 201)
        nid = c.json()["id"]
        self.assertIsNone(c.json()["lida_em"])

        r_read = self.client.post(f"/api/v1/notificacoes/{nid}/lida/", format="json")
        self.assertEqual(r_read.status_code, 200)
        self.assertIsNotNone(r_read.json()["lida_em"])

        self.client.post(
            "/api/v1/notificacoes/",
            {"nivel": "error", "titulo": "E1"},
            format="json",
        )
        self.client.post(
            "/api/v1/notificacoes/",
            {"nivel": "info", "titulo": "I1"},
            format="json",
        )

        r_all_read = self.client.post(
            "/api/v1/notificacoes/marcar-todas-lidas/", format="json"
        )
        self.assertEqual(r_all_read.status_code, 200)
        self.assertEqual(
            NotificacaoUsuario.objects.filter(usuario=self.user_a, lida_em__isnull=True).count(),
            0,
        )

    def test_cannot_read_other_user_notification(self):
        n = NotificacaoUsuario.objects.create(
            usuario=self.user_b,
            nivel=NotificacaoUsuario.Nivel.INFO,
            titulo="B only",
        )
        self.client.force_authenticate(self.user_a)
        r = self.client.post(f"/api/v1/notificacoes/{n.id}/lida/", format="json")
        self.assertEqual(r.status_code, 404)
