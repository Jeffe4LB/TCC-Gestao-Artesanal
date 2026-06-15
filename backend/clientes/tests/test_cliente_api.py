from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from clientes.models import Cliente


class ClienteApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="Passw0rd!",
        )
        self.client.force_authenticate(self.user)

    def test_crud_cliente(self):
        r_create = self.client.post(
            "/api/v1/clientes/",
            {
                "nome": "Maria Artesanato",
                "documento": "12345678901",
                "telefone": "41999990000",
                "email": "maria@example.com",
                "endereco": "Rua A, 1",
                "ativo": True,
            },
            format="json",
        )
        self.assertEqual(r_create.status_code, 201)
        cliente_id = r_create.json()["id"]
        self.assertEqual(r_create.json()["nome"], "Maria Artesanato")

        r_list = self.client.get("/api/v1/clientes/?search=Maria", format="json")
        self.assertEqual(r_list.status_code, 200)
        self.assertGreaterEqual(r_list.json()["total"], 1)

        r_patch = self.client.patch(
            f"/api/v1/clientes/{cliente_id}/",
            {"telefone": "41988887777"},
            format="json",
        )
        self.assertEqual(r_patch.status_code, 200)
        self.assertEqual(r_patch.json()["telefone"], "41988887777")

        r_delete = self.client.delete(f"/api/v1/clientes/{cliente_id}/", format="json")
        self.assertEqual(r_delete.status_code, 204)
        self.assertFalse(Cliente.objects.filter(pk=cliente_id).exists())
