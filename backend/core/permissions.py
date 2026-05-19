from rest_framework import permissions

from .capabilities import user_has_capability


class HasCapability(permissions.BasePermission):
    """Exige autenticação JWT e a capacidade definida em `required_capability` na view."""

    message = "Você não tem permissão para esta ação."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        cap = getattr(view, "required_capability", None)
        if cap is None:
            return True
        return user_has_capability(request.user, cap)


class HasManageUsers(permissions.BasePermission):
    message = "Apenas administradores podem gerenciar usuários."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return user_has_capability(request.user, "manage_users")
