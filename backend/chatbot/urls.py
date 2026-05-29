from . import views
from django.urls import path



urlpatterns = [
    path('', views.conversations, name='conversations'),
    path('<int:pk>/', views.conversation_detail, name='conversation_detail'),
    path('<int:conversation_id>/messages/', views.chatbot, name='chatbot'),
]