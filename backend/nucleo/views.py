import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .capabilities import dicionario_capacidades
from .models import PerfilUsuario, TokenRedefinicaoSenha
from .password_reset import (
    consumir_token,
    encontrar_usuario_por_uid_b64,
    smtp_pronto_para_redefinicao,
    tentar_enviar_emails_redefinicao,
)
from .permissions import TemPermissaoGerenciarUsuarios
from .serializers import (
    CadastroSerializer,
    ConfirmacaoRedefinicaoSenhaSerializer,
    SolicitacaoRedefinicaoSenhaSerializer,
    TrocaSenhaInicialSerializer,
    UsuarioAdminCriacaoSerializer,
    UsuarioAdminEscritaSerializer,
    UsuarioAdminLeituraSerializer,
)
from .services import criar_usuario_admin, excluir_usuario, resetar_senha_admin

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response(
        {
            "status": "ok",
            "service": "gestao-artesanal-api",
            "version": "v1",
        }
    )


class LoginTokenObtainPairView(TokenObtainPairView):
    """Mesma view de obtenção de JWT, com throttle dedicado ao login.

    Usa o escopo `login` declarado em `REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]`
    (default 10/min) para barrar força bruta. O cliente recebe HTTP 429 ao
    estourar o limite.
    """

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"


class CadastroView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "register"

    def post(self, request):
        serializer = CadastroSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            user = serializer.save()
        logger.info(
            "auth_register ok user_id=%s username=%s email=%r",
            user.pk,
            user.username,
            user.email or "",
        )
        payload = {"id": user.id, "username": user.username, "email": user.email}
        if settings.DEBUG:
            db = settings.DATABASES["default"]
            payload["_debug_database"] = f"{db.get('ENGINE', '')} | {db.get('NAME', '')}"
        return Response(payload, status=status.HTTP_201_CREATED)


class SolicitacaoRedefinicaoSenhaView(APIView):
    """Envia e-mail com link para redefinição (não revela se o e-mail existe)."""

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset"

    def post(self, request):
        serializer = SolicitacaoRedefinicaoSenhaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].strip().lower()
        tentar_enviar_emails_redefinicao(request, email)
        payload = {
            "detail": "Se existir uma conta com esse e-mail, enviaremos instruções em instantes."
        }
        if settings.DEBUG and not smtp_pronto_para_redefinicao():
            payload["dev_notice"] = (
                "SMTP sem credenciais completas: defina EMAIL_HOST_PASSWORD no .env "
                "(senha de app do Gmail, sem espaços) ou use "
                "EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend — "
                "o link de redefinição aparecerá no terminal do runserver."
            )
        return Response(payload)


class ConfirmacaoRedefinicaoSenhaView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset"

    def post(self, request):
        serializer = ConfirmacaoRedefinicaoSenhaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uid_b64 = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]
        user = encontrar_usuario_por_uid_b64(uid_b64)
        if user is None:
            return Response(
                {"detail": "Link inválido ou expirado."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not consumir_token(user, token):
            return Response(
                {"detail": "Link inválido, expirado ou já utilizado."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.set_password(new_password)
        user.save()
        try:
            perfil = user.perfil_usuario
            if perfil.senha_temporaria:
                perfil.senha_temporaria = False
                perfil.save(update_fields=["senha_temporaria"])
        except PerfilUsuario.DoesNotExist:
            pass
        TokenRedefinicaoSenha.objects.filter(usuario=user).delete()
        return Response(
            {"detail": "Senha alterada com sucesso. Você já pode entrar."}
        )


class UsuarioAdminViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """Gestão de usuários pelo administrador (listar, criar, editar, excluir)."""

    permission_classes = [IsAuthenticated, TemPermissaoGerenciarUsuarios]
    queryset = User.objects.all().order_by("username").select_related("perfil_usuario")
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    pagination_class = None

    def get_serializer_class(self):
        if self.action in ("update", "partial_update"):
            return UsuarioAdminEscritaSerializer
        return UsuarioAdminLeituraSerializer

    def create(self, request, *args, **kwargs):
        serializer = UsuarioAdminCriacaoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user, _ = criar_usuario_admin(
                **serializer.validated_data,
                criado_por=request.user,
            )
        except DjangoValidationError as exc:
            msg = exc.messages[0] if getattr(exc, "messages", None) else str(exc)
            return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)
        leitura = UsuarioAdminLeituraSerializer(user)
        return Response(leitura.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        try:
            excluir_usuario(user, executor=request.user)
        except DjangoValidationError as exc:
            msg = exc.messages[0] if getattr(exc, "messages", None) else str(exc)
            return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path="resetar-senha")
    def resetar_senha(self, request, pk=None):
        user = self.get_object()
        try:
            resultado = resetar_senha_admin(user)
        except DjangoValidationError as exc:
            msg = exc.messages[0] if getattr(exc, "messages", None) else str(exc)
            return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)
        if resultado.get("email_enviado"):
            return Response(
                {
                    "detail": "Nova senha temporária enviada por e-mail.",
                    "email_enviado": True,
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "detail": resultado.get(
                    "aviso",
                    "Senha alterada, mas o e-mail não foi enviado.",
                ),
                "email_enviado": False,
            },
            status=status.HTTP_200_OK,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    u = request.user
    senha_temporaria = False
    try:
        perfil = u.perfil_usuario
        papel = perfil.papel
        senha_temporaria = perfil.senha_temporaria
    except PerfilUsuario.DoesNotExist:
        papel = PerfilUsuario.Papel.EMPREENDEDOR
    return Response(
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "papel": papel,
            "senha_temporaria": senha_temporaria,
            "capacidades": dicionario_capacidades(u),
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def trocar_senha_inicial(request):
    serializer = TrocaSenhaInicialSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        perfil = request.user.perfil_usuario
    except PerfilUsuario.DoesNotExist:
        return Response(
            {"detail": "Perfil de usuário não encontrado."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not perfil.senha_temporaria:
        return Response(
            {"detail": "Troca obrigatória de senha não se aplica a esta conta."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    request.user.set_password(serializer.validated_data["new_password"])
    request.user.save()
    perfil.senha_temporaria = False
    perfil.save(update_fields=["senha_temporaria"])
    return Response({"detail": "Senha alterada com sucesso."})


# Aliases legados (urls)
RegisterView = CadastroView
PasswordResetRequestView = SolicitacaoRedefinicaoSenhaView
PasswordResetConfirmView = ConfirmacaoRedefinicaoSenhaView
AdminUserViewSet = UsuarioAdminViewSet
