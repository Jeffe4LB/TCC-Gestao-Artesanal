from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import serializers

from .models import UserProfile

_PROFILE_WRITABLE = (
    "role",
    "collab_master_data",
    "collab_stock_read",
    "collab_stock_movements",
    "collab_recipes_production",
    "collab_finance",
    "collab_reports",
    "collab_dashboard",
)


class AdminUserReadSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    collab_master_data = serializers.SerializerMethodField()
    collab_stock_read = serializers.SerializerMethodField()
    collab_stock_movements = serializers.SerializerMethodField()
    collab_recipes_production = serializers.SerializerMethodField()
    collab_finance = serializers.SerializerMethodField()
    collab_reports = serializers.SerializerMethodField()
    collab_dashboard = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "is_active",
            "role",
            "collab_master_data",
            "collab_stock_read",
            "collab_stock_movements",
            "collab_recipes_production",
            "collab_finance",
            "collab_reports",
            "collab_dashboard",
        )
        read_only_fields = ("id", "username")

    def _profile(self, obj):
        try:
            return obj.userprofile
        except UserProfile.DoesNotExist:
            return None

    def get_role(self, obj):
        p = self._profile(obj)
        return p.role if p else UserProfile.Role.ENTREPRENEUR

    def get_collab_master_data(self, obj):
        p = self._profile(obj)
        return p.collab_master_data if p else False

    def get_collab_stock_read(self, obj):
        p = self._profile(obj)
        return p.collab_stock_read if p else True

    def get_collab_stock_movements(self, obj):
        p = self._profile(obj)
        return p.collab_stock_movements if p else True

    def get_collab_recipes_production(self, obj):
        p = self._profile(obj)
        return p.collab_recipes_production if p else False

    def get_collab_finance(self, obj):
        p = self._profile(obj)
        return p.collab_finance if p else True

    def get_collab_reports(self, obj):
        p = self._profile(obj)
        return p.collab_reports if p else False

    def get_collab_dashboard(self, obj):
        p = self._profile(obj)
        return p.collab_dashboard if p else True


class AdminUserWriteSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(
        choices=UserProfile.Role.choices, required=False, write_only=False
    )
    collab_master_data = serializers.BooleanField(required=False)
    collab_stock_read = serializers.BooleanField(required=False)
    collab_stock_movements = serializers.BooleanField(required=False)
    collab_recipes_production = serializers.BooleanField(required=False)
    collab_finance = serializers.BooleanField(required=False)
    collab_reports = serializers.BooleanField(required=False)
    collab_dashboard = serializers.BooleanField(required=False)

    class Meta:
        model = User
        fields = (
            "email",
            "is_active",
            "role",
            "collab_master_data",
            "collab_stock_read",
            "collab_stock_movements",
            "collab_recipes_production",
            "collab_finance",
            "collab_reports",
            "collab_dashboard",
        )

    def to_representation(self, instance):
        return AdminUserReadSerializer(instance).data

    def validate(self, attrs):
        instance = self.instance
        profile, _ = UserProfile.objects.get_or_create(
            user=instance,
            defaults={"role": UserProfile.Role.ENTREPRENEUR},
        )
        role_after = attrs.get("role", profile.role)
        active_after = attrs.get("is_active", instance.is_active)
        if profile.role == UserProfile.Role.ADMIN and (
            role_after != UserProfile.Role.ADMIN or not active_after
        ):
            others = (
                User.objects.filter(
                    is_active=True,
                    userprofile__role=UserProfile.Role.ADMIN,
                )
                .exclude(pk=instance.pk)
                .exists()
            )
            if not others:
                raise serializers.ValidationError(
                    "Deve existir pelo menos um administrador ativo no sistema."
                )
        return attrs

    def update(self, instance, validated_data):
        profile_data = {}
        for k in _PROFILE_WRITABLE:
            if k in validated_data:
                profile_data[k] = validated_data.pop(k)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        profile = instance.userprofile
        for attr, val in profile_data.items():
            setattr(profile, attr, val)
        profile.save()
        return instance


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
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


class RegisterSerializer(serializers.Serializer):
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
        # Mesma normalização que `User.save()` / `create_user` (domínio em minúsculas, etc.).
        n = User.objects.normalize_email(str(value).strip())
        if not n:
            return ""
        qs = User.objects.filter(email__iexact=n)
        if qs.exists():
            count = qs.count()
            if settings.DEBUG:
                raise serializers.ValidationError(
                    f"Este e-mail já está associado a {count} conta(s). "
                    f"Na pasta do backend: python3 manage.py list_auth_users --email \"{n}\" "
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
