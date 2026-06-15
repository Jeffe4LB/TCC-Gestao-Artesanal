"""Capacidades da API (alinhadas ao menu e às telas)."""

from .models import PerfilUsuario

CAPACIDADES = (
    "gerenciar_usuarios",
    "dados_mestres",
    "estoque_leitura",
    "estoque_movimentacoes",
    "receitas_producao",
    "financeiro",
    "relatorios",
    "painel",
)

# Compatibilidade com chaves legadas em inglês (views antigas / testes)
_ALIASES_CAPACIDADE = {
    "manage_users": "gerenciar_usuarios",
    "master_data": "dados_mestres",
    "stock_read": "estoque_leitura",
    "stock_movements": "estoque_movimentacoes",
    "recipes_production": "receitas_producao",
    "finance": "financeiro",
    "reports": "relatorios",
    "dashboard": "painel",
}

CAPABILITIES = CAPACIDADES


def _normalizar_capacidade(capability: str) -> str:
    return _ALIASES_CAPACIDADE.get(capability, capability)


def usuario_tem_capacidade(user, capability: str) -> bool:
    capability = _normalizar_capacidade(capability)
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    try:
        p: PerfilUsuario = user.perfil_usuario
    except PerfilUsuario.DoesNotExist:
        return False

    if p.papel == PerfilUsuario.Papel.ADMIN:
        return True
    if p.papel == PerfilUsuario.Papel.EMPREENDEDOR:
        return capability != "gerenciar_usuarios"

    if p.papel == PerfilUsuario.Papel.COLABORADOR:
        mapa = {
            "gerenciar_usuarios": False,
            "dados_mestres": p.colaborador_dados_mestres,
            "estoque_leitura": p.colaborador_estoque_leitura,
            "estoque_movimentacoes": p.colaborador_estoque_movimentacoes,
            "receitas_producao": p.colaborador_receitas_producao,
            "financeiro": p.colaborador_financeiro,
            "relatorios": p.colaborador_relatorios,
            "painel": p.colaborador_painel,
        }
        return bool(mapa.get(capability, False))

    return False


def dicionario_capacidades(user) -> dict[str, bool]:
    return {c: usuario_tem_capacidade(user, c) for c in CAPACIDADES}


user_has_capability = usuario_tem_capacidade
capabilities_dict = dicionario_capacidades
