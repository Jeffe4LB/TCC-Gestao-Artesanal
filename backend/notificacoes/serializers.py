from rest_framework import serializers

from .models import NotificacaoUsuario


class NotificacaoUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificacaoUsuario
        fields = (
            "id",
            "nivel",
            "tipo",
            "titulo",
            "mensagem",
            "referencia_app",
            "referencia_id",
            "data_referencia",
            "lida_em",
            "criado_em",
        )
        read_only_fields = (
            "id",
            "tipo",
            "referencia_app",
            "referencia_id",
            "data_referencia",
            "lida_em",
            "criado_em",
        )


class NotificacaoUsuarioCriacaoSerializer(serializers.ModelSerializer):
    """Permite criar notificações genéricas manualmente via API.

    Campos de referência e dedup são preenchidos automaticamente pelo
    backend (tipo = `generica`, sem chave_dedup) para não conflitar com
    as notificações geradas por signals/management commands.
    """

    class Meta:
        model = NotificacaoUsuario
        fields = ("id", "nivel", "titulo", "mensagem", "lida_em", "criado_em")
        read_only_fields = ("id", "lida_em", "criado_em")


# Aliases legados
UserNotificationSerializer = NotificacaoUsuarioSerializer
UserNotificationCreateSerializer = NotificacaoUsuarioCriacaoSerializer
