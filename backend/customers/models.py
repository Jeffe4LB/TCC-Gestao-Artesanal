from django.db import models


class Customer(models.Model):
    name = models.CharField("nome", max_length=200)
    document = models.CharField("CPF/CNPJ", max_length=20, blank=True)
    phone = models.CharField("telefone", max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField("endereço", blank=True)
    is_active = models.BooleanField("ativo", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "cliente"
        verbose_name_plural = "clientes"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
