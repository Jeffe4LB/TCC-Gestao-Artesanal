from django.contrib import admin

from .models import PerfilUsuario, TokenRedefinicaoSenha


@admin.register(TokenRedefinicaoSenha)
class TokenRedefinicaoSenhaAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "criado_em", "expira_em", "usado_em")
    list_filter = ("usado_em",)
    search_fields = ("usuario__username", "usuario__email")
    readonly_fields = ("hash_token", "criado_em", "expira_em", "usado_em")
    raw_id_fields = ("usuario",)


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ("usuario", "papel")
    list_filter = ("papel",)
    search_fields = ("usuario__username", "usuario__email")
    raw_id_fields = ("usuario",)
