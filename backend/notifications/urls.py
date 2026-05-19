from django.urls import path

from .views import (
    NotificationSummaryView,
    UserNotificationListCreateView,
    UserNotificationMarkAllReadView,
    UserNotificationMarkReadView,
)

urlpatterns = [
    path("notifications/summary/", NotificationSummaryView.as_view(), name="notifications-summary"),
    path("notifications/read-all/", UserNotificationMarkAllReadView.as_view(), name="notifications-read-all"),
    path(
        "notifications/<int:pk>/read/",
        UserNotificationMarkReadView.as_view(),
        name="notifications-mark-read",
    ),
    path("notifications/", UserNotificationListCreateView.as_view(), name="notifications-list"),
]
