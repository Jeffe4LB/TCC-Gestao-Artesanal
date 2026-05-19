import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .capabilities import capabilities_dict
from .models import PasswordResetToken, UserProfile
from .password_reset import (
    consume_token,
    find_user_from_uid_b64,
    smtp_ready_for_password_reset,
    try_send_reset_emails,
)
from .permissions import HasManageUsers
from .serializers import (
    AdminUserReadSerializer,
    AdminUserWriteSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
)

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


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
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


class PasswordResetRequestView(APIView):
    """Envia e-mail com link para redefinição (não revela se o e-mail existe)."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].strip().lower()
        try_send_reset_emails(request, email)
        payload = {
            "detail": "Se existir uma conta com esse e-mail, enviaremos instruções em instantes."
        }
        if settings.DEBUG and not smtp_ready_for_password_reset():
            payload["dev_notice"] = (
                "SMTP sem credenciais completas: defina EMAIL_HOST_PASSWORD no .env "
                "(senha de app do Gmail, sem espaços) ou use "
                "EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend — "
                "o link de redefinição aparecerá no terminal do runserver."
            )
        return Response(payload)


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uid_b64 = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]
        user = find_user_from_uid_b64(uid_b64)
        if user is None:
            return Response(
                {"detail": "Link inválido ou expirado."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not consume_token(user, token):
            return Response(
                {"detail": "Link inválido, expirado ou já utilizado."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.set_password(new_password)
        user.save()
        PasswordResetToken.objects.filter(user=user).delete()
        return Response(
            {"detail": "Senha alterada com sucesso. Você já pode entrar."}
        )


class AdminUserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """Listagem e edição de usuários (apenas administrador)."""

    permission_classes = [IsAuthenticated, HasManageUsers]
    queryset = User.objects.all().order_by("username").select_related("userprofile")
    http_method_names = ["get", "patch", "head", "options"]
    pagination_class = None

    def get_serializer_class(self):
        if self.action in ("update", "partial_update"):
            return AdminUserWriteSerializer
        return AdminUserReadSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    u = request.user
    try:
        role = u.userprofile.role
    except UserProfile.DoesNotExist:
        role = UserProfile.Role.ENTREPRENEUR
    return Response(
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": role,
            "capabilities": capabilities_dict(u),
        }
    )
