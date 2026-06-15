from django.urls import path

from .views import (
    NotificacaoUsuarioListaCriacaoView,
    NotificacaoUsuarioMarcarLidaView,
    NotificacaoUsuarioMarcarTodasLidasView,
    ResumoNotificacoesView,
)

urlpatterns = [
    path("notificacoes/resumo/", ResumoNotificacoesView.as_view(), name="notificacoes-resumo"),
    path(
        "notificacoes/marcar-todas-lidas/",
        NotificacaoUsuarioMarcarTodasLidasView.as_view(),
        name="notificacoes-marcar-todas-lidas",
    ),
    path(
        "notificacoes/<int:pk>/lida/",
        NotificacaoUsuarioMarcarLidaView.as_view(),
        name="notificacoes-marcar-lida",
    ),
    path("notificacoes/", NotificacaoUsuarioListaCriacaoView.as_view(), name="notificacoes-lista"),
]
