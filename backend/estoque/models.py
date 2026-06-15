from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from produtos.models import Produto


class SaldoEstoque(models.Model):
    produto = models.OneToOneField(
        Produto,
        on_delete=models.CASCADE,
        related_name="saldo_estoque",
        verbose_name="produto",
    )
    quantidade = models.DecimalField(
        "quantidade",
        max_digits=14,
        decimal_places=3,
        default=0,
    )
    quantidade_reservada = models.DecimalField(
        "quantidade reservada",
        max_digits=14,
        decimal_places=3,
        default=0,
        help_text="Comprometida por pedidos/rascunhos futuros; não reduz o saldo físico.",
    )

    class Meta:
        db_table = "estoque_saldoestoque"
        verbose_name = "saldo de estoque"
        verbose_name_plural = "saldos de estoque"

    @property
    def disponivel(self) -> Decimal:
        return self.quantidade - self.quantidade_reservada

    def __str__(self) -> str:
        return f"{self.produto.sku}: {self.quantidade}"


class MovimentacaoEstoque(models.Model):
    class TipoMovimentacao(models.TextChoices):
        ENTRADA_COMPRA = "purchase_in", "Entrada (compra)"
        AJUSTE = "adjustment", "Ajuste manual"
        CONSUMO_PRODUCAO = "production_consumption", "Consumo (produção)"
        ENTRADA_PRODUCAO = "production_output", "Entrada produto acabado (produção)"
        VENDA_RECEBER = "receivable_sale", "Saída (venda / conta a receber)"
        ESTORNO_VENDA_RECEBER = "receivable_sale_reversal", "Estorno (conta a receber)"
        ESTORNO_ENTRADA_PRODUCAO = (
            "production_output_reversal",
            "Estorno entrada produto acabado (produção)",
        )
        ESTORNO_CONSUMO_PRODUCAO = (
            "production_consumption_reversal",
            "Estorno consumo insumo (produção)",
        )

    produto = models.ForeignKey(
        Produto,
        on_delete=models.PROTECT,
        related_name="movimentacoes_estoque",
        verbose_name="produto",
    )
    delta_quantidade = models.DecimalField(
        "variação (unidade base)",
        max_digits=14,
        decimal_places=3,
        help_text="Sempre na unidade base da categoria do produto (KG, L ou UN).",
    )
    quantidade_informada = models.DecimalField(
        "quantidade informada",
        max_digits=14,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Magnitude informada pelo usuário (opcional em lançamentos legados).",
    )
    unidade_informada = models.CharField(
        "unidade informada",
        max_length=3,
        blank=True,
        null=True,
        help_text="Unidade da quantidade informada (mesma categoria da unidade de cadastro do produto).",
    )
    tipo_movimentacao = models.CharField(
        "tipo",
        max_length=40,
        choices=TipoMovimentacao.choices,
    )
    ordem_producao = models.ForeignKey(
        "OrdemProducao",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movimentacoes_estoque",
        verbose_name="produção",
    )
    conta_receber = models.ForeignKey(
        "financeiro.ContaReceber",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimentacoes_estoque",
        verbose_name="conta a receber",
    )
    conta_pagar = models.ForeignKey(
        "financeiro.ContaPagar",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimentacoes_estoque",
        verbose_name="conta a pagar",
    )
    venda_receber_substituta = models.BooleanField(
        "baixa de venda substituída",
        default=False,
        help_text="Marcado quando um estorno por edição ou cancelamento desfez o efeito desta saída.",
    )
    producao_substituta = models.BooleanField(
        "movimento de produção substituído",
        default=False,
        help_text="Marcado quando um cancelamento desfez o efeito deste movimento.",
    )
    observacoes = models.TextField("observações", blank=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimentacoes_estoque_criadas",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "estoque_movimentacaoestoque"
        verbose_name = "movimentação"
        verbose_name_plural = "movimentações"
        ordering = ["-criado_em", "-id"]
        indexes = [
            models.Index(fields=["criado_em", "produto"], name="est_mov_criado_prod"),
            models.Index(fields=["tipo_movimentacao", "criado_em"], name="est_mov_tipo_criado"),
            models.Index(fields=["produto", "criado_em"], name="est_mov_prod_criado"),
        ]

    def __str__(self) -> str:
        return f"{self.produto.sku} {self.delta_quantidade} ({self.tipo_movimentacao})"


class Receita(models.Model):
    """Receita — insumos por 1 unidade do produto fabricado."""

    produto = models.OneToOneField(
        Produto,
        on_delete=models.CASCADE,
        related_name="receita",
        verbose_name="produto fabricado",
    )
    observacoes = models.TextField("observações", blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "estoque_receita"
        verbose_name = "receita"
        verbose_name_plural = "receitas"

    def __str__(self) -> str:
        return f"Receita: {self.produto.sku}"

    def clean(self) -> None:
        super().clean()
        if self.produto_id and self.produto.tipo_produto != Produto.TipoProduto.FABRICADO:
            raise ValidationError(
                {"produto": "A receita só pode ser vinculada a produto fabricado manualmente."}
            )


class LinhaReceita(models.Model):
    receita = models.ForeignKey(
        Receita,
        on_delete=models.CASCADE,
        related_name="linhas",
        verbose_name="receita",
    )
    insumo = models.ForeignKey(
        Produto,
        on_delete=models.PROTECT,
        related_name="linhas_receita_insumo",
        verbose_name="insumo",
    )
    quantidade_por_unidade = models.DecimalField(
        "qtd por unidade fabricada",
        max_digits=14,
        decimal_places=3,
    )

    class Meta:
        db_table = "estoque_linhareceita"
        verbose_name = "linha da receita"
        verbose_name_plural = "linhas da receita"
        constraints = [
            models.UniqueConstraint(
                fields=["receita", "insumo"],
                name="unique_recipe_component",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.insumo.sku} × {self.quantidade_por_unidade}"

    def clean(self) -> None:
        super().clean()
        if self.receita_id and self.insumo_id and self.receita.produto_id == self.insumo_id:
            raise ValidationError({"insumo": "Insumo não pode ser o próprio produto fabricado."})


class OrdemProducao(models.Model):
    produto = models.ForeignKey(
        Produto,
        on_delete=models.PROTECT,
        related_name="ordens_producao",
        verbose_name="produto fabricado",
    )
    quantidade_produzida = models.DecimalField(
        "quantidade produzida",
        max_digits=14,
        decimal_places=3,
    )
    observacoes = models.TextField("observações", blank=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ordens_producao",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    cancelada_em = models.DateTimeField(
        "cancelada em",
        null=True,
        blank=True,
        help_text="Preenchido quando a ordem foi cancelada e o estoque estornado.",
    )
    cancelada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ordens_producao_canceladas",
        verbose_name="cancelada por",
    )

    class Meta:
        db_table = "estoque_ordemproducao"
        verbose_name = "lançamento de produção"
        verbose_name_plural = "lançamentos de produção"
        ordering = ["-criado_em", "-id"]

    @property
    def ativa(self) -> bool:
        return self.cancelada_em is None

    def __str__(self) -> str:
        return f"{self.produto.sku} +{self.quantidade_produzida}"


class LinhaOrdemProducao(models.Model):
    ordem = models.ForeignKey(
        OrdemProducao,
        on_delete=models.CASCADE,
        related_name="linhas",
        verbose_name="produção",
    )
    insumo = models.ForeignKey(
        Produto,
        on_delete=models.PROTECT,
        related_name="linhas_ordem_producao",
        verbose_name="insumo",
    )
    quantidade_consumida = models.DecimalField(
        "quantidade consumida",
        max_digits=14,
        decimal_places=3,
    )

    class Meta:
        db_table = "estoque_linhaordemproducao"
        verbose_name = "consumo na produção"
        verbose_name_plural = "consumos na produção"

    def __str__(self) -> str:
        return f"{self.insumo.sku} -{self.quantidade_consumida}"


# Aliases legados
StockBalance = SaldoEstoque
StockMovement = MovimentacaoEstoque
Recipe = Receita
RecipeLine = LinhaReceita
ProductionRun = OrdemProducao
ProductionRunLine = LinhaOrdemProducao
