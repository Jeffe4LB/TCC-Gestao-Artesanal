from django.contrib import admin

from .models import Categoria, Fornecedor, Produto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nome", "criado_em")
    search_fields = ("nome",)


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ("nome", "documento", "telefone", "email", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome", "razao_social", "documento", "email")


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = (
        "sku",
        "nome",
        "categoria",
        "tipo_produto",
        "unidade",
        "preco_venda",
        "custo_unitario",
        "estoque_minimo",
        "ativo",
    )
    list_filter = ("tipo_produto", "ativo", "categoria")
    search_fields = ("sku", "nome", "descricao")
    raw_id_fields = ("categoria", "fornecedor")
