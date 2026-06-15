from rest_framework import permissions

from .capabilities import usuario_tem_capacidade


class TemCapacidade(permissions.BasePermission):
    """Exige autenticação JWT e a capacidade definida em `required_capability` na view."""

    message = "Você não tem permissão para esta ação."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        cap = getattr(view, "required_capability", None)
        if cap is None:
            return True
        return usuario_tem_capacidade(request.user, cap)


class TemCapacidadeFinanceiro(permissions.BasePermission):
    """Exige capacidade financeiro (histórico de parceiros, etc.)."""

    message = "Você não tem permissão para consultar o financeiro."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return usuario_tem_capacidade(request.user, "financeiro")


class TemPermissaoGerenciarUsuarios(permissions.BasePermission):
    message = "Apenas administradores podem gerenciar usuários."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return usuario_tem_capacidade(request.user, "gerenciar_usuarios")


