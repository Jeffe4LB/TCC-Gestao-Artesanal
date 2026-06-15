from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from estoque.models import MovimentacaoEstoque
from nucleo.models import PerfilUsuario
from produtos.models import Categoria, Fornecedor, Produto


def _criar_admin(username="admin", password="Admin12345!", email="admin@test.com"):
    user = User.objects.create_user(
        username=username, password=password, email=email, is_active=True
    )
    perfil = user.perfil_usuario
    perfil.papel = PerfilUsuario.Papel.ADMIN
    perfil.save()
    return user


def _criar_colaborador(username="colab", email="colab@test.com"):
    user = User.objects.create_user(
        username=username, password="Colab12345!", email=email, is_active=True
    )
    perfil = user.perfil_usuario
    perfil.papel = PerfilUsuario.Papel.COLABORADOR
    perfil.save()
    return user


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class UsuariosAdminApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = _criar_admin()
        self.client.force_authenticate(user=self.admin)
        mail.outbox.clear()

    def test_admin_cria_usuario_com_senha_temporaria(self):
        response = self.client.post(
            "/api/v1/auth/users/",
            {
                "nome": "João Silva",
                "email": "joao@exemplo.com",
                "papel": PerfilUsuario.Papel.COLABORADOR,
                "colaborador_relatorios": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        usuario = User.objects.get(username="joao@exemplo.com")
        self.assertTrue(usuario.perfil_usuario.senha_temporaria)
        self.assertEqual(usuario.first_name, "João Silva")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("joao@exemplo.com", mail.outbox[0].body)

    def test_nao_cria_email_duplicado(self):
        _criar_colaborador(email="dup@test.com")
        response = self.client.post(
            "/api/v1/auth/users/",
            {
                "nome": "Outro",
                "email": "dup@test.com",
                "papel": PerfilUsuario.Papel.COLABORADOR,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_nao_exclui_ultimo_admin(self):
        response = self.client.delete(f"/api/v1/auth/users/{self.admin.pk}/")
        self.assertEqual(response.status_code, 400)
        self.assertIn("último administrador", response.data["detail"].lower())
        self.assertTrue(User.objects.filter(pk=self.admin.pk).exists())

    def test_nao_exclui_a_si_mesmo(self):
        outro = _criar_admin(username="admin2", email="admin2@test.com")
        self.client.force_authenticate(user=outro)
        response = self.client.delete(f"/api/v1/auth/users/{outro.pk}/")
        self.assertEqual(response.status_code, 400)
        self.assertIn("você não pode", response.data["detail"].lower())

    def test_exclui_colaborador_sem_movimentacoes(self):
        colab = _criar_colaborador(username="del", email="del@test.com")
        response = self.client.delete(f"/api/v1/auth/users/{colab.pk}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(User.objects.filter(pk=colab.pk).exists())

    def test_nao_exclui_usuario_com_movimentacoes(self):
        colab = _criar_colaborador(username="mov", email="mov@test.com")
        cat = Categoria.objects.create(nome="Cat")
        forn = Fornecedor.objects.create(nome="Forn")
        prod = Produto.objects.create(
            sku="P1",
            nome="Prod",
            categoria=cat,
            fornecedor=forn,
            unidade="UN",
            preco_venda=Decimal("1"),
            custo_aquisicao=Decimal("1"),
            custo_unitario=Decimal("1"),
        )
        MovimentacaoEstoque.objects.create(
            produto=prod,
            delta_quantidade=Decimal("1"),
            tipo_movimentacao=MovimentacaoEstoque.TipoMovimentacao.AJUSTE,
            criado_por=colab,
        )
        response = self.client.delete(f"/api/v1/auth/users/{colab.pk}/")
        self.assertEqual(response.status_code, 400)
        self.assertIn("movimentações", response.data["detail"].lower())
        self.assertTrue(User.objects.filter(pk=colab.pk).exists())

    def test_resetar_senha_marca_temporaria_e_envia_email(self):
        colab = _criar_colaborador()
        colab.perfil_usuario.senha_temporaria = False
        colab.perfil_usuario.save()
        mail.outbox.clear()
        response = self.client.post(f"/api/v1/auth/users/{colab.pk}/resetar-senha/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["email_enviado"])
        colab.perfil_usuario.refresh_from_db()
        self.assertTrue(colab.perfil_usuario.senha_temporaria)
        self.assertEqual(len(mail.outbox), 1)

    def test_resetar_senha_mantem_alteracao_se_email_falhar(self):
        colab = _criar_colaborador(username="semail", email="semail@test.com")
        with patch("nucleo.services.enviar_boas_vindas", side_effect=RuntimeError("smtp down")):
            response = self.client.post(f"/api/v1/auth/users/{colab.pk}/resetar-senha/")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["email_enviado"])
        colab.perfil_usuario.refresh_from_db()
        self.assertTrue(colab.perfil_usuario.senha_temporaria)

    def test_me_inclui_senha_temporaria(self):
        self.admin.perfil_usuario.senha_temporaria = True
        self.admin.perfil_usuario.save()
        response = self.client.get("/api/v1/auth/me/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["senha_temporaria"])

    def test_trocar_senha_inicial_limpa_flag(self):
        colab = _criar_colaborador(username="troca", email="troca@test.com")
        colab.perfil_usuario.senha_temporaria = True
        colab.perfil_usuario.save()
        self.client.force_authenticate(user=colab)
        response = self.client.post(
            "/api/v1/auth/trocar-senha-inicial/",
            {
                "new_password": "NovaSenha!99",
                "new_password_confirm": "NovaSenha!99",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        colab.perfil_usuario.refresh_from_db()
        self.assertFalse(colab.perfil_usuario.senha_temporaria)
        colab.refresh_from_db()
        self.assertTrue(colab.check_password("NovaSenha!99"))

    def test_colaborador_sem_permissao_403(self):
        colab = _criar_colaborador()
        self.client.force_authenticate(user=colab)
        response = self.client.get("/api/v1/auth/users/")
        self.assertEqual(response.status_code, 403)
