from django.db import migrations


def seed_balances(apps, schema_editor):
    Product = apps.get_model("produtos", "Product")
    StockBalance = apps.get_model("estoque", "StockBalance")
    for p in Product.objects.all():
        StockBalance.objects.get_or_create(product_id=p.pk, defaults={"quantity": 0})


def unseed(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("estoque", "0001_initial"),
        ("produtos", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_balances, unseed),
    ]
