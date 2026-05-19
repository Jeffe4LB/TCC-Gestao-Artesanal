from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from products.models import Product


class StockBalance(models.Model):
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name="stock_balance",
        verbose_name="produto",
    )
    quantity = models.DecimalField("quantidade", max_digits=14, decimal_places=3, default=0)

    class Meta:
        verbose_name = "saldo de estoque"
        verbose_name_plural = "saldos de estoque"

    def __str__(self) -> str:
        return f"{self.product.sku}: {self.quantity}"


class StockMovement(models.Model):
    class MovementType(models.TextChoices):
        PURCHASE_IN = "purchase_in", "Entrada (compra)"
        ADJUSTMENT = "adjustment", "Ajuste manual"
        PRODUCTION_CONSUMPTION = "production_consumption", "Consumo (produção)"
        PRODUCTION_OUTPUT = "production_output", "Entrada produto acabado (produção)"
        RECEIVABLE_SALE = "receivable_sale", "Saída (venda / conta a receber)"
        RECEIVABLE_SALE_REVERSAL = "receivable_sale_reversal", "Estorno (conta a receber)"

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="stock_movements",
        verbose_name="produto",
    )
    quantity_delta = models.DecimalField(
        "variação (unidade base)",
        max_digits=14,
        decimal_places=3,
        help_text="Sempre na unidade base da categoria do produto (KG, L ou UN).",
    )
    quantity_input = models.DecimalField(
        "quantidade informada",
        max_digits=14,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Magnitude informada pelo usuário (opcional em lançamentos legados).",
    )
    unit_input = models.CharField(
        "unidade informada",
        max_length=3,
        blank=True,
        null=True,
        help_text="Unidade da quantidade informada (mesma categoria da unidade de cadastro do produto).",
    )
    movement_type = models.CharField(
        "tipo",
        max_length=40,
        choices=MovementType.choices,
    )
    production_run = models.ForeignKey(
        "ProductionRun",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="stock_movements",
        verbose_name="produção",
    )
    account_receivable = models.ForeignKey(
        "finance.AccountReceivable",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_movements",
        verbose_name="conta a receber",
    )
    receivable_sale_superseded = models.BooleanField(
        "baixa de venda substituída",
        default=False,
        help_text="True quando um estorno por edição/cancelamento desfez o efeito desta saída.",
    )
    notes = models.TextField("observações", blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_movements_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "movimentação"
        verbose_name_plural = "movimentações"
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"{self.product.sku} {self.quantity_delta} ({self.movement_type})"


class Recipe(models.Model):
    """Receita (BOM) — insumos por 1 unidade do produto fabricado."""

    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name="recipe",
        verbose_name="produto fabricado",
    )
    notes = models.TextField("observações", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "receita (BOM)"
        verbose_name_plural = "receitas (BOM)"

    def __str__(self) -> str:
        return f"Receita: {self.product.sku}"

    def clean(self) -> None:
        super().clean()
        if self.product_id and self.product.product_type != Product.ProductType.MANUFACTURED:
            raise ValidationError(
                {"product": "A receita só pode ser vinculada a produto fabricado manualmente."}
            )


class RecipeLine(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="lines",
        verbose_name="receita",
    )
    component = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="recipe_lines_as_component",
        verbose_name="insumo",
    )
    quantity_per_unit = models.DecimalField(
        "qtd por unidade fabricada",
        max_digits=14,
        decimal_places=3,
    )

    class Meta:
        verbose_name = "linha da receita"
        verbose_name_plural = "linhas da receita"
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "component"],
                name="unique_recipe_component",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.component.sku} × {self.quantity_per_unit}"

    def clean(self) -> None:
        super().clean()
        if self.recipe_id and self.component_id and self.recipe.product_id == self.component_id:
            raise ValidationError({"component": "Insumo não pode ser o próprio produto fabricado."})


class ProductionRun(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="production_runs",
        verbose_name="produto fabricado",
    )
    quantity_produced = models.DecimalField("quantidade produzida", max_digits=14, decimal_places=3)
    notes = models.TextField("observações", blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="production_runs",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "lançamento de produção"
        verbose_name_plural = "lançamentos de produção"
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"{self.product.sku} +{self.quantity_produced}"


class ProductionRunLine(models.Model):
    run = models.ForeignKey(
        ProductionRun,
        on_delete=models.CASCADE,
        related_name="lines",
        verbose_name="produção",
    )
    component = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="production_run_lines",
        verbose_name="insumo",
    )
    quantity_consumed = models.DecimalField("quantidade consumida", max_digits=14, decimal_places=3)

    class Meta:
        verbose_name = "consumo na produção"
        verbose_name_plural = "consumos na produção"

    def __str__(self) -> str:
        return f"{self.component.sku} -{self.quantity_consumed}"
