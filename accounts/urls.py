from django.urls import path

from .views import (
    ForgotPasswordView,
    ForgotPasswordDoneView,
    ForgotPasswordConfirmView,
    ForgotPasswordCompleteView,
)

from . import views

app_name = "accounts"

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("login/", views.login_view, name="login"),
    path("auth/", views.auth_split, name="auth_split"),
    path("logout/", views.logout_view, name="logout"),
    path("password-reset/", ForgotPasswordView.as_view(), name="password_reset"),
    path(
        "password-reset/done/",
        ForgotPasswordDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        ForgotPasswordConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        ForgotPasswordCompleteView.as_view(),
        name="password_reset_complete",
    ),
]
