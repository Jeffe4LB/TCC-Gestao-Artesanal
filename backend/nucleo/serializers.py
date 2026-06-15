from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import serializers

from .models import PerfilUsuario

_PERFIL_EDITAVEL = (
    "papel",
    "colaborador_dados_mestres",
    "colaborador_estoque_leitura",
    "colaborador_estoque_movimentacoes",
    "colaborador_receitas_producao",
    "colaborador_financeiro",
    "colaborador_relatorios",
    "colaborador_painel",
)


class UsuarioAdminLeituraSerializer(serializers.ModelSerializer):
    papel = serializers.SerializerMethodField()
    colaborador_dados_mestres = serializers.SerializerMethodField()
    colaborador_estoque_leitura = serializers.SerializerMethodField()
    colaborador_estoque_movimentacoes = serializers.SerializerMethodField()
    colaborador_receitas_producao = serializers.SerializerMethodField()
    colaborador_financeiro = serializers.SerializerMethodField()
    colaborador_relatorios = serializers.SerializerMethodField()
    colaborador_painel = serializers.SerializerMethodField()
    ativo = serializers.BooleanField(source="is_active")

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "ativo",
            "papel",
            "colaborador_dados_mestres",
            "colaborador_estoque_leitura",
            "colaborador_estoque_movimentacoes",
            "colaborador_receitas_producao",
            "colaborador_financeiro",
            "colaborador_relatorios",
            "colaborador_painel",
        )
        read_only_fields = ("id", "username")

    def _perfil(self, obj):
        try:
            return obj.perfil_usuario
        except PerfilUsuario.DoesNotExist:
            return None

    def get_papel(self, obj):
        p = self._perfil(obj)
        return p.papel if p else PerfilUsuario.Papel.EMPREENDEDOR

    def get_colaborador_dados_mestres(self, obj):
        p = self._perfil(obj)
        return p.colaborador_dados_mestres if p else False

    def get_colaborador_estoque_leitura(self, obj):
        p = self._perfil(obj)
        return p.colaborador_estoque_leitura if p else True

    def get_colaborador_estoque_movimentacoes(self, obj):
        p = self._perfil(obj)
        return p.colaborador_estoque_movimentacoes if p else True

    def get_colaborador_receitas_producao(self, obj):
        p = self._perfil(obj)
        return p.colaborador_receitas_producao if p else False

    def get_colaborador_financeiro(self, obj):
        p = self._perfil(obj)
        return p.colaborador_financeiro if p else True

    def get_colaborador_relatorios(self, obj):
        p = self._perfil(obj)
        return p.colaborador_relatorios if p else False

    def get_colaborador_painel(self, obj):
        p = self._perfil(obj)
        return p.colaborador_painel if p else True


class UsuarioAdminEscritaSerializer(serializers.ModelSerializer):
    papel = serializers.ChoiceField(
        choices=PerfilUsuario.Papel.choices, required=False, write_only=False
    )
    colaborador_dados_mestres = serializers.BooleanField(required=False)
    colaborador_estoque_leitura = serializers.BooleanField(required=False)
    colaborador_estoque_movimentacoes = serializers.BooleanField(required=False)
    colaborador_receitas_producao = serializers.BooleanField(required=False)
    colaborador_financeiro = serializers.BooleanField(required=False)
    colaborador_relatorios = serializers.BooleanField(required=False)
    colaborador_painel = serializers.BooleanField(required=False)
    ativo = serializers.BooleanField(source="is_active", required=False)

    class Meta:
        model = User
        fields = (
            "email",
            "ativo",
            "papel",
            "colaborador_dados_mestres",
            "colaborador_estoque_leitura",
            "colaborador_estoque_movimentacoes",
            "colaborador_receitas_producao",
            "colaborador_financeiro",
            "colaborador_relatorios",
            "colaborador_painel",
        )

    def to_representation(self, instance):
        return UsuarioAdminLeituraSerializer(instance).data

    def validate(self, attrs):
        instance = self.instance
        perfil, _ = PerfilUsuario.objects.get_or_create(
            usuario=instance,
            defaults={"papel": PerfilUsuario.Papel.EMPREENDEDOR},
        )
        papel_depois = attrs.get("papel", perfil.papel)
        ativo_depois = attrs.get("is_active", instance.is_active)
        if perfil.papel == PerfilUsuario.Papel.ADMIN and (
            papel_depois != PerfilUsuario.Papel.ADMIN or not ativo_depois
        ):
            outros = (
                User.objects.filter(
                    is_active=True,
                    perfil_usuario__papel=PerfilUsuario.Papel.ADMIN,
                )
                .exclude(pk=instance.pk)
                .exists()
            )
            if not outros:
                raise serializers.ValidationError(
                    "Deve existir pelo menos um administrador ativo no sistema."
                )
        return attrs

    def update(self, instance, validated_data):
        dados_perfil = {}
        for k in _PERFIL_EDITAVEL:
            if k in validated_data:
                dados_perfil[k] = validated_data.pop(k)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        perfil = instance.perfil_usuario
        for attr, val in dados_perfil.items():
            setattr(perfil, attr, val)
        perfil.save()
        return instance


class UsuarioAdminCriacaoSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    papel = serializers.ChoiceField(choices=PerfilUsuario.Papel.choices)
    colaborador_dados_mestres = serializers.BooleanField(required=False, default=False)
    colaborador_estoque_leitura = serializers.BooleanField(required=False, default=True)
    colaborador_estoque_movimentacoes = serializers.BooleanField(required=False, default=True)
    colaborador_receitas_producao = serializers.BooleanField(required=False, default=False)
    colaborador_financeiro = serializers.BooleanField(required=False, default=True)
    colaborador_relatorios = serializers.BooleanField(required=False, default=False)
    colaborador_painel = serializers.BooleanField(required=False, default=True)


class TrocaSenhaInicialSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "As senhas não coincidem."}
            )
        return attrs


class SolicitacaoRedefinicaoSenhaSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ConfirmacaoRedefinicaoSenhaSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "As senhas não coincidem."}
            )
        return attrs


class CadastroSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField(required=False, allow_blank=True, default="")

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Este nome de usuário já está em uso.")
        return value

    def validate_email(self, value):
        if value is None or not str(value).strip():
            return ""
        n = User.objects.normalize_email(str(value).strip())
        if not n:
            return ""
        qs = User.objects.filter(email__iexact=n)
        if qs.exists():
            count = qs.count()
            if settings.DEBUG:
                raise serializers.ValidationError(
                    f"Este e-mail já está associado a {count} conta(s). "
                    f"Na pasta do backend: python3 manage.py listar_usuarios_auth --email \"{n}\" "
                    "(confirme que edita a mesma base que o runserver — ver cabeçalho do comando)."
                )
            raise serializers.ValidationError(
                "Este e-mail já está em uso. Se acabou de alterar dados na base, confirme que não há "
                "outra linha em auth_user com o mesmo e-mail e que está a ver a mesma base de dados do servidor."
            )
        return n

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
            email=validated_data.get("email") or "",
        )


# Aliases legados
AdminUserReadSerializer = UsuarioAdminLeituraSerializer
AdminUserWriteSerializer = UsuarioAdminEscritaSerializer
PasswordResetRequestSerializer = SolicitacaoRedefinicaoSenhaSerializer
PasswordResetConfirmSerializer = ConfirmacaoRedefinicaoSenhaSerializer
RegisterSerializer = CadastroSerializer
