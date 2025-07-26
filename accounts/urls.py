from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("login/", views.login_view, name="login"),
    path("auth/", views.auth_split, name="auth_split"),
    path("logout/", views.logout_view, name="logout"),
    path("reader_dashboard/", views.reader_dashboard, name="reader_dashboard"),
    path("author_dashboard/", views.author_dashboard, name="author_dashboard"),
    path("author_management/", views.author_management, name="author_management"),
]
