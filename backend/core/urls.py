from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from .views import (
    AdminUserViewSet,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RegisterView,
    health,
    me,
)

router = DefaultRouter()
router.register("auth/users", AdminUserViewSet, basename="admin-user")

urlpatterns = [
    path("health/", health),
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("auth/register/", RegisterView.as_view(), name="auth_register"),
    path(
        "auth/password/forgot/",
        PasswordResetRequestView.as_view(),
        name="auth_password_forgot",
    ),
    path(
        "auth/password/reset/",
        PasswordResetRequestView.as_view(),
        name="auth_password_reset",
    ),
    path(
        "auth/password/reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="auth_password_reset_confirm",
    ),
    path("auth/me/", me, name="auth_me"),
    path("", include(router.urls)),
]
