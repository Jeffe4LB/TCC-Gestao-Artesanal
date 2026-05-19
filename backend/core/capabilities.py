"""Capacidades da API (alinhadas ao menu e às telas)."""

from .models import UserProfile

CAPABILITIES = (
    "manage_users",
    "master_data",
    "stock_read",
    "stock_movements",
    "recipes_production",
    "finance",
    "reports",
    "dashboard",
)


def user_has_capability(user, capability: str) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    try:
        p: UserProfile = user.userprofile
    except UserProfile.DoesNotExist:
        return False

    if p.role == UserProfile.Role.ADMIN:
        return True
    if p.role == UserProfile.Role.ENTREPRENEUR:
        return capability != "manage_users"

    if p.role == UserProfile.Role.COLLABORATOR:
        collab_map = {
            "manage_users": False,
            "master_data": p.collab_master_data,
            "stock_read": p.collab_stock_read,
            "stock_movements": p.collab_stock_movements,
            "recipes_production": p.collab_recipes_production,
            "finance": p.collab_finance,
            "reports": p.collab_reports,
            "dashboard": p.collab_dashboard,
        }
        return bool(collab_map.get(capability, False))

    return False


def capabilities_dict(user) -> dict[str, bool]:
    return {c: user_has_capability(user, c) for c in CAPABILITIES}
