from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("nucleo", "0005_fase5_rotular_apps_pt"),
    ]

    operations = [
        migrations.AddField(
            model_name="perfilusuario",
            name="senha_temporaria",
            field=models.BooleanField(
                default=False,
                help_text="Obriga troca de senha no próximo acesso após login.",
                verbose_name="senha temporária",
            ),
        ),
    ]
