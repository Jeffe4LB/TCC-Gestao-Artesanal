"""Lista utilizadores na base `default` (a mesma que o `runserver` usa nesta pasta)."""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Lista id, username, e-mail e flags (útil para confirmar registo e superuser)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            dest="email",
            default="",
            help="Mostrar só contas cujo e-mail coincide (após normalização Django) com este valor.",
        )

    def handle(self, *args, **options):
        User = get_user_model()
        db = settings.DATABASES["default"]
        engine = db.get("ENGINE", "")
        name = db.get("NAME", "")
        self.stdout.write(self.style.WARNING(f"Base em uso: ENGINE={engine}"))
        self.stdout.write(self.style.WARNING(f"              NAME={name!r}"))
        self.stdout.write("")

        qs = User.objects.order_by("id")
        email_filter = (options.get("email") or "").strip()
        if email_filter:
            needle = User.objects.normalize_email(email_filter)
            qs = qs.filter(email__iexact=needle)
            self.stdout.write(
                self.style.NOTICE(
                    f"Filtro e-mail normalizado={needle!r} — {qs.count()} conta(s)."
                )
            )
        n = qs.count()
        self.stdout.write(self.style.NOTICE(f"Total de linhas a mostrar: {n}"))
        if not n:
            self.stdout.write("Nenhum registo em auth_user com esse critério.")
            return
        for u in qs:
            self.stdout.write(
                f"  id={u.pk}  username={u.username!r}  email={u.email!r}  "
                f"superuser={u.is_superuser}  staff={u.is_staff}  active={u.is_active}"
            )
