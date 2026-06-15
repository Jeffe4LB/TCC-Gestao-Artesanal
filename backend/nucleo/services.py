"""Regras de negócio para gestão administrativa de usuários."""

from __future__ import annotations

import logging
import secrets

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction

from estoque.models import MovimentacaoEstoque

from .emails import enviar_boas_vindas
from .models import PerfilUsuario

logger = logging.getLogger(__name__)

User = get_user_model()

_CAMPOS_COLABORADOR = (
    "colaborador_dados_mestres",
    "colaborador_estoque_leitura",
    "colaborador_estoque_movimentacoes",
    "colaborador_receitas_producao",
    "colaborador_financeiro",
    "colaborador_relatorios",
    "colaborador_painel",
)


def _email_normalizado(email: str) -> str:
    return User.objects.normalize_email(email.strip())


def _aplicar_flags_colaborador(perfil: PerfilUsuario, dados: dict) -> None:
    for campo in _CAMPOS_COLABORADOR:
        if campo in dados:
            setattr(perfil, campo, dados[campo])


@transaction.atomic
def criar_usuario_admin(
    *,
    nome: str,
    email: str,
    papel: str,
    colaborador_dados_mestres: bool = False,
    colaborador_estoque_leitura: bool = True,
    colaborador_estoque_movimentacoes: bool = True,
    colaborador_receitas_producao: bool = False,
    colaborador_financeiro: bool = True,
    colaborador_relatorios: bool = False,
    colaborador_painel: bool = True,
    criado_por: User | None = None,
) -> tuple[User, str]:
    del criado_por  # reservado para auditoria futura
    email_norm = _email_normalizado(email)
    if not email_norm:
        raise ValidationError("Informe um e-mail válido.")
    if User.objects.filter(username__iexact=email_norm).exists():
        raise ValidationError("E-mail já cadastrado.")
    if User.objects.filter(email__iexact=email_norm).exists():
        raise ValidationError("E-mail já cadastrado.")

    senha_temp = secrets.token_urlsafe(12)
    user = User.objects.create_user(
        username=email_norm,
        email=email_norm,
        first_name=(nome or "").strip()[:150],
        password=senha_temp,
        is_active=True,
    )
    perfil = user.perfil_usuario
    perfil.papel = papel
    perfil.senha_temporaria = True
    _aplicar_flags_colaborador(
        perfil,
        {
            "colaborador_dados_mestres": colaborador_dados_mestres,
            "colaborador_estoque_leitura": colaborador_estoque_leitura,
            "colaborador_estoque_movimentacoes": colaborador_estoque_movimentacoes,
            "colaborador_receitas_producao": colaborador_receitas_producao,
            "colaborador_financeiro": colaborador_financeiro,
            "colaborador_relatorios": colaborador_relatorios,
            "colaborador_painel": colaborador_painel,
        },
    )
    perfil.save()

    try:
        enviar_boas_vindas(user=user, senha_temporaria=senha_temp)
    except Exception:
        logger.exception("boas_vindas falhou user_id=%s", user.pk)
        raise ValidationError(
            "Não foi possível enviar o e-mail de boas-vindas. "
            "Verifique SMTP ou tente resetar a senha depois."
        ) from None

    return user, senha_temp


def validar_pode_excluir(user: User) -> None:
    if user.is_superuser:
        raise ValidationError("Não é possível excluir superusuário.")

    try:
        perfil = user.perfil_usuario
    except PerfilUsuario.DoesNotExist:
        perfil = None

    if perfil and perfil.papel == PerfilUsuario.Papel.ADMIN:
        outros = (
            User.objects.filter(
                is_active=True,
                perfil_usuario__papel=PerfilUsuario.Papel.ADMIN,
            )
            .exclude(pk=user.pk)
            .exists()
        )
        if not outros:
            raise ValidationError(
                "Não é possível excluir o último administrador ativo."
            )

    if MovimentacaoEstoque.objects.filter(criado_por=user).exists():
        raise ValidationError(
            "Usuário possui movimentações de estoque registradas. "
            "Inative a conta em vez de excluir."
        )


@transaction.atomic
def excluir_usuario(user: User, *, executor: User) -> None:
    validar_pode_excluir(user)
    if user.pk == executor.pk:
        raise ValidationError("Você não pode excluir a si mesmo.")
    user.delete()


def resetar_senha_admin(user: User) -> dict:
    """
    Gera senha temporária e tenta enviar por e-mail.
    A alteração no banco é confirmada mesmo se o SMTP falhar.
    """
    nova_senha = secrets.token_urlsafe(12)
    with transaction.atomic():
        user.set_password(nova_senha)
        user.save(update_fields=["password"])
        perfil = user.perfil_usuario
        perfil.senha_temporaria = True
        perfil.save(update_fields=["senha_temporaria"])

    try:
        enviar_boas_vindas(user=user, senha_temporaria=nova_senha)
        return {"email_enviado": True}
    except Exception:
        logger.exception("boas_vindas reset falhou user_id=%s", user.pk)
        return {
            "email_enviado": False,
            "aviso": (
                "Senha temporária definida, mas o e-mail não foi enviado. "
                "Verifique SMTP no .env ou use "
                "EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend "
                "em desenvolvimento (a senha aparece no terminal do runserver)."
            ),
        }
