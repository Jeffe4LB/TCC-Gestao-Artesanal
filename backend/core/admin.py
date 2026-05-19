from django.contrib import admin

from .models import PasswordResetToken, UserProfile


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "created_at", "expires_at", "used_at")
    list_filter = ("used_at",)
    search_fields = ("user__username", "user__email")
    readonly_fields = ("user", "token_hash", "created_at", "expires_at", "used_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "role",
        "collab_master_data",
        "collab_stock_read",
        "collab_stock_movements",
        "collab_recipes_production",
        "collab_finance",
        "collab_reports",
        "collab_dashboard",
    )
    list_filter = ("role",)
    search_fields = ("user__username", "user__email")
    raw_id_fields = ("user",)
