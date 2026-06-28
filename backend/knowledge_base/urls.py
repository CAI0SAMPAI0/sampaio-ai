from django.urls import path
from .views import SemanticSearchView

urlpatterns = [
    path('search/', SemanticSearchView.as_view(), name='semantic-search'),
]
