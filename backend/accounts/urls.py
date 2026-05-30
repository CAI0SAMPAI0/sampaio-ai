from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from accounts.views import register, logout, profile, update_profile, change_password

urlpatterns = [
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', register, name='register'),
    path('logout/', logout, name='logout'),
    path('me/', profile, name='profile'),
    path('me/password/', change_password, name='change_password'),
    path('me/update/', update_profile, name='update_profile'),
]