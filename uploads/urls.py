from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import KnowledgeDocumentViewSet

router = DefaultRouter()
router.register(r"documents", KnowledgeDocumentViewSet, basename="knowledge-document")

urlpatterns = [
    path("", include(router.urls)),
]
