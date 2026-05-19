from django.db.models.signals import post_save
from django.dispatch import receiver

from products.models import Product

from .models import StockBalance


@receiver(post_save, sender=Product)
def create_empty_stock_balance(sender, instance: Product, created: bool, **kwargs) -> None:
    if created:
        StockBalance.objects.get_or_create(product=instance, defaults={"quantity": 0})
