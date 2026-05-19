from django.conf import settings
from django.db import models
from django.utils import timezone

from customers.models import Customer
from products.models import Product, Supplier


class AccountPayable(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Em aberto"
        PAID = "paid", "Pago"
        CANCELLED = "cancelled", "Cancelado"

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accounts_payable",
        verbose_name="fornecedor",
    )
    description = models.CharField("descrição", max_length=300)
    amount = models.DecimalField("valor", max_digits=14, decimal_places=2)
    due_date = models.DateField("vencimento")
    status = models.CharField(
        "status",
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
    )
    paid_at = models.DateField("pago em", null=True, blank=True)
    notes = models.TextField("observações", blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accounts_payable_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "conta a pagar"
        verbose_name_plural = "contas a pagar"
        ordering = ["due_date", "id"]

    def __str__(self) -> str:
        return f"Pagar {self.description} ({self.amount})"


def _default_issue_date():
    return timezone.now().date()


class AccountReceivable(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Em aberto"
        PAID = "paid", "Recebido"
        CANCELLED = "cancelled", "Cancelado"

    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accounts_receivable",
        verbose_name="cliente",
    )
    description = models.CharField("descrição", max_length=300)
    issue_date = models.DateField(
        "emissão",
        default=_default_issue_date,
        help_text="Data do documento / pedido.",
    )
    amount = models.DecimalField(
        "valor total",
        max_digits=14,
        decimal_places=2,
        help_text="Soma das linhas; atualizado ao salvar.",
    )
    due_date = models.DateField("vencimento")
    status = models.CharField(
        "status",
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
    )
    received_at = models.DateField("recebido em", null=True, blank=True)
    notes = models.TextField("observações", blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accounts_receivable_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "conta a receber"
        verbose_name_plural = "contas a receber"
        ordering = ["due_date", "id"]

    def __str__(self) -> str:
        return f"Receber {self.description} ({self.amount})"


class AccountReceivableLine(models.Model):
    """Itens de um lançamento de contas a receber (vários produtos por cliente)."""

    receivable = models.ForeignKey(
        AccountReceivable,
        on_delete=models.CASCADE,
        related_name="lines",
        verbose_name="lançamento",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="receivable_lines",
        verbose_name="produto",
        help_text="Obrigatório em novos lançamentos; nulo apenas em registros migrados.",
    )
    quantity = models.DecimalField("quantidade", max_digits=14, decimal_places=6)
    unit = models.CharField("unidade", max_length=3)
    unit_price = models.DecimalField("preço unitário", max_digits=14, decimal_places=2)
    discount = models.DecimalField("desconto (R$)", max_digits=14, decimal_places=2, default=0)
    line_total = models.DecimalField("total da linha (R$)", max_digits=14, decimal_places=2, default=0)

    class Meta:
        verbose_name = "linha a receber"
        verbose_name_plural = "linhas a receber"
        ordering = ["id"]

    def __str__(self) -> str:
        return f"{self.receivable_id}: {self.product_id or '—'} × {self.quantity}"
