from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import (
    MeView,
    MeUpdateView,
    ChangePasswordView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
)

urlpatterns = [
    # JWT Auth
    path("login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("refresh", TokenRefreshView.as_view(), name="token_refresh"),
    # User Profile
    path("me", MeView.as_view(), name="user_me"),
    path("me/update", MeUpdateView.as_view(), name="user_me_update"),
    path("me/password", ChangePasswordView.as_view(), name="user_change_password"),
    # Password Recovery
    path(
        "password-reset",
        PasswordResetRequestView.as_view(),
        name="password_reset_request",
    ),
    path(
        "password-reset/confirm",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
]
