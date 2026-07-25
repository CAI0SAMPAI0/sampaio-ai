from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StudyPlanViewSet

router = DefaultRouter()
router.register(r"", StudyPlanViewSet, basename="studyplan")

urlpatterns = [
    path("", include(router.urls)),
]
