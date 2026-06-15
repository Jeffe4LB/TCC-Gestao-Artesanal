from django.contrib import admin

from .models import (
    LinhaOrdemProducao,
    LinhaReceita,
    MovimentacaoEstoque,
    OrdemProducao,
    Receita,
    SaldoEstoque,
)


@admin.register(SaldoEstoque)
class SaldoEstoqueAdmin(admin.ModelAdmin):
    list_display = ("produto", "quantidade")
    search_fields = ("produto__sku", "produto__nome")
    raw_id_fields = ("produto",)


@admin.register(MovimentacaoEstoque)
class MovimentacaoEstoqueAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "produto",
        "delta_quantidade",
        "tipo_movimentacao",
        "producao_substituta",
        "criado_em",
    )
    list_filter = ("tipo_movimentacao",)
    search_fields = ("produto__sku", "observacoes")
    raw_id_fields = ("produto", "ordem_producao", "criado_por")
    readonly_fields = ("criado_em",)


class LinhaReceitaInline(admin.TabularInline):
    model = LinhaReceita
    extra = 0
    raw_id_fields = ("insumo",)


@admin.register(Receita)
class ReceitaAdmin(admin.ModelAdmin):
    list_display = ("produto", "atualizado_em")
    search_fields = ("produto__sku", "produto__nome")
    raw_id_fields = ("produto",)
    inlines = [LinhaReceitaInline]


@admin.register(OrdemProducao)
class OrdemProducaoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "produto",
        "quantidade_produzida",
        "criado_em",
        "cancelada_em",
        "criado_por",
    )
    list_filter = ("criado_em", "cancelada_em")
    search_fields = ("produto__sku", "observacoes")
    raw_id_fields = ("produto", "criado_por", "cancelada_por")
    readonly_fields = ("criado_em", "cancelada_em")


@admin.register(LinhaOrdemProducao)
class LinhaOrdemProducaoAdmin(admin.ModelAdmin):
    list_display = ("ordem", "insumo", "quantidade_consumida")
    raw_id_fields = ("ordem", "insumo")
