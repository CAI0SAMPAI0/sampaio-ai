from . import views
from django.urls import path



urlpatterns = [
    path('api/chat/', views.chatbot, name='chatbot'),
]