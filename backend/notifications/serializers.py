from rest_framework import serializers

from .models import UserNotification


class UserNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNotification
        fields = ("id", "level", "title", "body", "read_at", "created_at")
        read_only_fields = ("id", "read_at", "created_at")


class UserNotificationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNotification
        fields = ("id", "level", "title", "body", "read_at", "created_at")
        read_only_fields = ("id", "read_at", "created_at")
