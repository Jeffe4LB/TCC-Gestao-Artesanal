from rest_framework import serializers

from .models import Cliente


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = (
            "id",
            "nome",
            "documento",
            "telefone",
            "email",
            "endereco",
            "ativo",
            "criado_em",
            "atualizado_em",
        )
        read_only_fields = ("id", "criado_em", "atualizado_em")
