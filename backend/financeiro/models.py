from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from clientes.models import Cliente
from produtos.models import Fornecedor, Produto


class DocumentoFinanceiro(models.Model):
    """Cabeçalho lógico que agrupa N parcelas (contas a pagar ou receber)."""

    class Tipo(models.TextChoices):
        PAGAR = "payable", "A pagar"
        RECEBER = "receivable", "A receber"

    class Situacao(models.TextChoices):
        ABERTO = "open", "Em aberto"
        QUITADO = "settled", "Quitado"
        CANCELADO = "cancelled", "Cancelado"

    tipo = models.CharField("tipo", max_length=20, choices=Tipo.choices)
    fornecedor = models.ForeignKey(
        Fornecedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documentos_financeiros",
        verbose_name="fornecedor",
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documentos_financeiros",
        verbose_name="cliente",
    )
    descricao = models.CharField("descrição", max_length=300)
    valor_total = models.DecimalField("valor total", max_digits=14, decimal_places=2)
    numero_parcelas = models.PositiveSmallIntegerField("número de parcelas", default=1)
    data_emissao = models.DateField("data de emissão")
    situacao = models.CharField(
        "situação",
        max_length=20,
        choices=Situacao.choices,
        default=Situacao.ABERTO,
    )
    observacoes = models.TextField("observações", blank=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documentos_financeiros_criados",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "financeiro_documentofinanceiro"
        verbose_name = "documento financeiro"
        verbose_name_plural = "documentos financeiros"
        ordering = ["-data_emissao", "-id"]

    def __str__(self) -> str:
        return f"Doc {self.get_tipo_display()} {self.descricao} ({self.valor_total})"


class ContaPagar(models.Model):
    class Situacao(models.TextChoices):
        ABERTO = "open", "Em aberto"
        PARCIAL = "partial", "Parcialmente pago"
        PAGO = "paid", "Pago"
        CANCELADO = "cancelled", "Cancelado"

    documento = models.ForeignKey(
        DocumentoFinanceiro,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="contas_pagar",
        verbose_name="documento",
    )
    fornecedor = models.ForeignKey(
        Fornecedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contas_pagar",
        verbose_name="fornecedor",
    )
    descricao = models.CharField("descrição", max_length=300)
    valor = models.DecimalField("valor", max_digits=14, decimal_places=2)
    valor_pago = models.DecimalField(
        "valor pago",
        max_digits=14,
        decimal_places=2,
        default=Decimal("0"),
        help_text="Soma das baixas parciais; quando igual ao valor, a parcela está quitada.",
    )
    numero_parcela = models.PositiveSmallIntegerField(
        "nº parcela",
        default=1,
        help_text="Índice desta parcela no documento (1..N).",
    )
    total_parcelas = models.PositiveSmallIntegerField(
        "total parcelas",
        default=1,
        help_text="Quantidade total de parcelas do documento.",
    )
    vencimento = models.DateField("vencimento")
    situacao = models.CharField(
        "situação",
        max_length=20,
        choices=Situacao.choices,
        default=Situacao.ABERTO,
    )
    pago_em = models.DateField("pago em", null=True, blank=True)
    observacoes = models.TextField("observações", blank=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contas_pagar_criadas",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "financeiro_contapagar"
        verbose_name = "conta a pagar"
        verbose_name_plural = "contas a pagar"
        ordering = ["vencimento", "id"]
        indexes = [
            models.Index(fields=["situacao", "vencimento"], name="fin_pagar_sit_venc"),
            models.Index(fields=["fornecedor", "situacao"], name="fin_pagar_forn_sit"),
            models.Index(fields=["pago_em"], name="fin_pagar_pago_em"),
        ]

    @property
    def saldo_restante(self) -> Decimal:
        return self.valor - self.valor_pago

    def __str__(self) -> str:
        return f"Pagar {self.descricao} ({self.valor})"


class LinhaContaPagar(models.Model):
    """Itens de uma conta a pagar gerada por entrada de estoque (compra)."""

    conta_pagar = models.ForeignKey(
        ContaPagar,
        on_delete=models.CASCADE,
        related_name="linhas",
        verbose_name="lançamento",
    )
    produto = models.ForeignKey(
        Produto,
        on_delete=models.PROTECT,
        related_name="linhas_conta_pagar",
        verbose_name="produto",
    )
    quantidade = models.DecimalField("quantidade", max_digits=14, decimal_places=6)
    unidade = models.CharField("unidade", max_length=3)
    custo_unitario = models.DecimalField(
        "custo unitário (unid. cadastro)",
        max_digits=14,
        decimal_places=2,
        help_text="Custo por 1 unidade de cadastro do produto.",
    )
    total_linha = models.DecimalField(
        "total da linha (R$)",
        max_digits=14,
        decimal_places=2,
        default=0,
    )

    class Meta:
        db_table = "financeiro_linhacontapagar"
        verbose_name = "linha a pagar"
        verbose_name_plural = "linhas a pagar"
        ordering = ["id"]

    def __str__(self) -> str:
        return f"{self.conta_pagar_id}: {self.produto_id} × {self.quantidade}"


def _default_data_emissao():
    return timezone.now().date()


_default_issue_date = _default_data_emissao


class ContaReceber(models.Model):
    class Situacao(models.TextChoices):
        ABERTO = "open", "Em aberto"
        PARCIAL = "partial", "Parcialmente recebido"
        RECEBIDO = "paid", "Recebido"
        CANCELADO = "cancelled", "Cancelado"

    documento = models.ForeignKey(
        DocumentoFinanceiro,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="contas_receber",
        verbose_name="documento",
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contas_receber",
        verbose_name="cliente",
    )
    descricao = models.CharField("descrição", max_length=300)
    data_emissao = models.DateField(
        "emissão",
        default=_default_data_emissao,
        help_text="Data do documento / pedido.",
    )
    valor = models.DecimalField(
        "valor total",
        max_digits=14,
        decimal_places=2,
        help_text="Soma das linhas; atualizado ao salvar.",
    )
    valor_pago = models.DecimalField(
        "valor recebido",
        max_digits=14,
        decimal_places=2,
        default=Decimal("0"),
        help_text="Soma das baixas parciais; quando igual ao valor, a parcela está quitada.",
    )
    numero_parcela = models.PositiveSmallIntegerField(
        "nº parcela",
        default=1,
        help_text="Índice desta parcela no documento (1..N).",
    )
    total_parcelas = models.PositiveSmallIntegerField(
        "total parcelas",
        default=1,
        help_text="Quantidade total de parcelas do documento.",
    )
    vencimento = models.DateField("vencimento")
    situacao = models.CharField(
        "situação",
        max_length=20,
        choices=Situacao.choices,
        default=Situacao.ABERTO,
    )
    recebido_em = models.DateField("recebido em", null=True, blank=True)
    observacoes = models.TextField("observações", blank=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contas_receber_criadas",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "financeiro_contareceber"
        verbose_name = "conta a receber"
        verbose_name_plural = "contas a receber"
        ordering = ["vencimento", "id"]
        indexes = [
            models.Index(fields=["situacao", "vencimento"], name="fin_receb_sit_venc"),
            models.Index(fields=["cliente", "situacao"], name="fin_receb_cli_sit"),
            models.Index(fields=["recebido_em"], name="fin_receb_recebido_em"),
        ]

    @property
    def saldo_restante(self) -> Decimal:
        return self.valor - self.valor_pago

    def __str__(self) -> str:
        return f"Receber {self.descricao} ({self.valor})"


class LinhaContaReceber(models.Model):
    """Itens de um lançamento de contas a receber (vários produtos por cliente)."""

    conta_receber = models.ForeignKey(
        ContaReceber,
        on_delete=models.CASCADE,
        related_name="linhas",
        verbose_name="lançamento",
    )
    produto = models.ForeignKey(
        Produto,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="linhas_conta_receber",
        verbose_name="produto",
        help_text="Obrigatório em novos lançamentos; nulo apenas em registros migrados.",
    )
    quantidade = models.DecimalField("quantidade", max_digits=14, decimal_places=6)
    unidade = models.CharField("unidade", max_length=3)
    preco_unitario = models.DecimalField("preço unitário", max_digits=14, decimal_places=2)
    desconto = models.DecimalField("desconto (R$)", max_digits=14, decimal_places=2, default=0)
    total_linha = models.DecimalField(
        "total da linha (R$)",
        max_digits=14,
        decimal_places=2,
        default=0,
    )

    class Meta:
        db_table = "financeiro_linhacontareceber"
        verbose_name = "linha a receber"
        verbose_name_plural = "linhas a receber"
        ordering = ["id"]

    def __str__(self) -> str:
        return f"{self.conta_receber_id}: {self.produto_id or '—'} × {self.quantidade}"


# Aliases legados
FinancialDocument = DocumentoFinanceiro
AccountPayable = ContaPagar
AccountPayableLine = LinhaContaPagar
AccountReceivable = ContaReceber
AccountReceivableLine = LinhaContaReceber
