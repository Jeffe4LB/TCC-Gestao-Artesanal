from django.db import models


class Cliente(models.Model):
    nome = models.CharField("nome", max_length=200)
    documento = models.CharField("CPF/CNPJ", max_length=20, blank=True)
    telefone = models.CharField("telefone", max_length=30, blank=True)
    email = models.EmailField(blank=True)
    endereco = models.TextField("endereço", blank=True)
    ativo = models.BooleanField("ativo", default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "clientes_cliente"
        verbose_name = "cliente"
        verbose_name_plural = "clientes"
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome
