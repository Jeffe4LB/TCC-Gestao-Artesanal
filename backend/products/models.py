from django.db import models

from core.units import UNIT_CODE_CHOICES


class Category(models.Model):
    name = models.CharField("nome", max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "categoria"
        verbose_name_plural = "categorias"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Supplier(models.Model):
    name = models.CharField("nome", max_length=200)
    legal_name = models.CharField("razão social", max_length=200, blank=True)
    document = models.CharField("CPF/CNPJ", max_length=20, blank=True)
    phone = models.CharField("telefone", max_length=30, blank=True)
    email = models.EmailField(blank=True)
    notes = models.TextField("observações", blank=True)
    is_active = models.BooleanField("ativo", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "fornecedor"
        verbose_name_plural = "fornecedores"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    class ProductType(models.TextChoices):
        PURCHASED = "purchased", "Comprado"
        MANUFACTURED = "manufactured", "Produzido manualmente"

    sku = models.CharField("SKU/código", max_length=64, unique=True)
    name = models.CharField("nome", max_length=200)
    description = models.TextField("descrição", blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name="categoria",
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        verbose_name="fornecedor",
    )
    product_type = models.CharField(
        "tipo",
        max_length=20,
        choices=ProductType.choices,
        default=ProductType.PURCHASED,
    )
    unit = models.CharField(
        "unidade",
        max_length=3,
        choices=UNIT_CODE_CHOICES,
        default="UN",
        help_text="Unidade de estoque/cadastro; saldo futuro será na base da categoria (KG, L ou UN).",
    )
    min_stock = models.DecimalField(
        "estoque mínimo",
        max_digits=14,
        decimal_places=3,
        default=0,
    )
    sale_price = models.DecimalField(
        "preço de venda (por unidade de cadastro)",
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text="Valor de venda por 1 unidade do produto (mesma unidade do campo unidade).",
    )
    purchase_unit_cost = models.DecimalField(
        "custo de aquisição (por unidade)",
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text="Produto comprado: custo para adquirir 1 unidade de cadastro. Fabricado: ignorado (use receita).",
    )
    unit_cost = models.DecimalField(
        "custo unitário atual",
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text="Comprado: espelha o custo de aquisição. Fabricado: soma dos custos da BOM (recalculado).",
    )
    is_active = models.BooleanField("ativo", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "produto"
        verbose_name_plural = "produtos"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.sku} — {self.name}"
