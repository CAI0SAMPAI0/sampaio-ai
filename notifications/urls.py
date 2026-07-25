from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, AuditLogViewSet

router = DefaultRouter()
router.register(r"logs", AuditLogViewSet, basename="auditlog")
router.register(r"", NotificationViewSet, basename="notification")

urlpatterns = [
    path("", include(router.urls)),
]
