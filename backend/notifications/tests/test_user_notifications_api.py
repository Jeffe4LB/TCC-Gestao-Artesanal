from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from notifications.models import UserNotification


class UserNotificationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_a = User.objects.create_user(username="a", password="Passw0rd!")
        self.user_b = User.objects.create_user(username="b", password="Passw0rd!")

    def test_list_only_own_and_unread_filter(self):
        UserNotification.objects.create(
            user=self.user_a,
            level=UserNotification.Level.INFO,
            title="A1",
        )
        n_unread = UserNotification.objects.create(
            user=self.user_a,
            level=UserNotification.Level.SUCCESS,
            title="A2",
        )
        read_n = UserNotification.objects.create(
            user=self.user_a,
            level=UserNotification.Level.WARNING,
            title="A3",
            read_at=timezone.now(),
        )

        UserNotification.objects.create(
            user=self.user_b,
            level=UserNotification.Level.ERROR,
            title="B1",
        )

        self.client.force_authenticate(self.user_a)
        r_all = self.client.get("/api/v1/notifications/", format="json")
        self.assertEqual(r_all.status_code, 200)
        self.assertEqual(r_all.json()["count"], 3)

        r_unread = self.client.get("/api/v1/notifications/?unread=1", format="json")
        self.assertEqual(r_unread.status_code, 200)
        self.assertEqual(r_unread.json()["count"], 2)
        ids = {row["id"] for row in r_unread.json()["results"]}
        self.assertIn(n_unread.id, ids)
        self.assertNotIn(read_n.id, ids)

    def test_create_mark_read_mark_all(self):
        self.client.force_authenticate(self.user_a)
        c = self.client.post(
            "/api/v1/notifications/",
            {"level": "success", "title": "OK", "body": "detalhe"},
            format="json",
        )
        self.assertEqual(c.status_code, 201)
        nid = c.json()["id"]
        self.assertIsNone(c.json()["read_at"])

        r_read = self.client.post(f"/api/v1/notifications/{nid}/read/", format="json")
        self.assertEqual(r_read.status_code, 200)
        self.assertIsNotNone(r_read.json()["read_at"])

        self.client.post(
            "/api/v1/notifications/",
            {"level": "error", "title": "E1"},
            format="json",
        )
        self.client.post(
            "/api/v1/notifications/",
            {"level": "info", "title": "I1"},
            format="json",
        )

        r_all_read = self.client.post("/api/v1/notifications/read-all/", format="json")
        self.assertEqual(r_all_read.status_code, 200)
        self.assertEqual(
            UserNotification.objects.filter(user=self.user_a, read_at__isnull=True).count(),
            0,
        )

    def test_cannot_read_other_user_notification(self):
        n = UserNotification.objects.create(
            user=self.user_b,
            level=UserNotification.Level.INFO,
            title="B only",
        )
        self.client.force_authenticate(self.user_a)
        r = self.client.post(f"/api/v1/notifications/{n.id}/read/", format="json")
        self.assertEqual(r.status_code, 404)
