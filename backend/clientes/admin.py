from django.contrib import admin

from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "documento", "telefone", "email", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome", "documento", "email", "telefone")
