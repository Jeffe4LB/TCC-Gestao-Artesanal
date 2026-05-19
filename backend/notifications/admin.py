from django.contrib import admin

from .models import UserNotification


@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "level", "title", "read_at", "created_at")
    list_filter = ("level", "read_at")
    search_fields = ("title", "body", "user__username")
    readonly_fields = ("created_at",)
