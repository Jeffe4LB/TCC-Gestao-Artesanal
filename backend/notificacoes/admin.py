from django.contrib import admin

from .models import NotificacaoUsuario


@admin.register(NotificacaoUsuario)
class NotificacaoUsuarioAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "nivel", "titulo", "lida_em", "criado_em")
    list_filter = ("nivel", "lida_em")
    search_fields = ("titulo", "mensagem", "usuario__username")
    readonly_fields = ("criado_em",)
