from django.db import models

from nucleo.units import UNIT_CODE_CHOICES


class Categoria(models.Model):
    nome = models.CharField("nome", max_length=120)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "produtos_categoria"
        verbose_name = "categoria"
        verbose_name_plural = "categorias"
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome


class Fornecedor(models.Model):
    nome = models.CharField("nome", max_length=200)
    razao_social = models.CharField("razão social", max_length=200, blank=True)
    documento = models.CharField("CPF/CNPJ", max_length=20, blank=True)
    telefone = models.CharField("telefone", max_length=30, blank=True)
    email = models.EmailField(blank=True)
    observacoes = models.TextField("observações", blank=True)
    ativo = models.BooleanField("ativo", default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "produtos_fornecedor"
        verbose_name = "fornecedor"
        verbose_name_plural = "fornecedores"
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome


class Produto(models.Model):
    class TipoProduto(models.TextChoices):
        COMPRADO = "purchased", "Comprado"
        FABRICADO = "manufactured", "Produzido manualmente"

    sku = models.CharField("Código (SKU)", max_length=64, unique=True)
    nome = models.CharField("nome", max_length=200)
    descricao = models.TextField("descrição", blank=True)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="produtos",
        verbose_name="categoria",
    )
    fornecedor = models.ForeignKey(
        Fornecedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="produtos",
        verbose_name="fornecedor",
    )
    tipo_produto = models.CharField(
        "tipo",
        max_length=20,
        choices=TipoProduto.choices,
        default=TipoProduto.COMPRADO,
    )
    unidade = models.CharField(
        "unidade",
        max_length=3,
        choices=UNIT_CODE_CHOICES,
        default="UN",
        help_text="Unidade de estoque/cadastro; saldo futuro será na base da categoria (KG, L ou UN).",
    )
    estoque_minimo = models.DecimalField(
        "estoque mínimo",
        max_digits=14,
        decimal_places=3,
        default=0,
    )
    preco_venda = models.DecimalField(
        "preço de venda (por unidade de cadastro)",
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text="Valor de venda por 1 unidade do produto (mesma unidade do campo unidade).",
    )
    custo_aquisicao = models.DecimalField(
        "custo de aquisição (por unidade)",
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text="Produto comprado: custo para adquirir 1 unidade de cadastro. Fabricado: ignorado (use receita).",
    )
    custo_unitario = models.DecimalField(
        "custo unitário atual",
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text="Comprado: espelha o custo de aquisição. Fabricado: soma dos custos da receita (recalculado).",
    )
    ativo = models.BooleanField("ativo", default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "produtos_produto"
        verbose_name = "produto"
        verbose_name_plural = "produtos"
        ordering = ["nome"]

    def __str__(self) -> str:
        return f"{self.sku} — {self.nome}"


class HistoricoPreco(models.Model):
    """Registro append-only de alterações de preço e custo unitário."""

    produto = models.ForeignKey(
        Produto,
        on_delete=models.CASCADE,
        related_name="historico_precos",
        verbose_name="produto",
    )
    preco_venda_anterior = models.DecimalField(
        "preço de venda anterior",
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
    )
    preco_venda_novo = models.DecimalField(
        "preço de venda novo",
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
    )
    custo_anterior = models.DecimalField(
        "custo unitário anterior",
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
    )
    custo_novo = models.DecimalField(
        "custo unitário novo",
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
    )
    alterado_por = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="historicos_preco_produto",
        verbose_name="alterado por",
    )
    alterado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "produtos_historicopreco"
        verbose_name = "histórico de preço"
        verbose_name_plural = "históricos de preço"
        ordering = ["-alterado_em"]
        indexes = [
            models.Index(fields=["produto", "alterado_em"], name="prod_hist_prec_em"),
        ]

    def __str__(self) -> str:
        return f"Histórico #{self.pk} produto={self.produto_id}"
