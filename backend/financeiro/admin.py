from django.contrib import admin

from .models import ContaPagar, ContaReceber, LinhaContaPagar, LinhaContaReceber


class LinhaContaPagarInline(admin.TabularInline):
    model = LinhaContaPagar
    extra = 0
    raw_id_fields = ("produto",)


class LinhaContaReceberInline(admin.TabularInline):
    model = LinhaContaReceber
    extra = 0
    raw_id_fields = ("produto",)


@admin.register(ContaPagar)
class ContaPagarAdmin(admin.ModelAdmin):
    list_display = ("descricao", "valor", "vencimento", "situacao", "pago_em", "fornecedor")
    list_filter = ("situacao", "vencimento")
    search_fields = ("descricao", "observacoes")
    raw_id_fields = ("fornecedor", "criado_por")
    date_hierarchy = "vencimento"
    inlines = [LinhaContaPagarInline]


@admin.register(ContaReceber)
class ContaReceberAdmin(admin.ModelAdmin):
    list_display = (
        "descricao",
        "data_emissao",
        "valor",
        "vencimento",
        "situacao",
        "recebido_em",
        "cliente",
    )
    list_filter = ("situacao", "vencimento")
    search_fields = ("descricao", "observacoes")
    raw_id_fields = ("cliente", "criado_por")
    date_hierarchy = "vencimento"
    inlines = [LinhaContaReceberInline]
