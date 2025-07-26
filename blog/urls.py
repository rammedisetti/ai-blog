from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('blog/', views.blog_home, name='blog_home'),
    path('blog/<slug:slug>/', views.article_detail, name='article_detail'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('privacy/', views.privacy, name='privacy'),
    path('terms/', views.terms, name='terms'),
    path('cancellation/', views.cancellation, name='cancellation'),
    path('add_post/', views.add_post, name='add_post'),
    path("toggle_like/<int:post_id>/", views.toggle_like, name="toggle_like"),
    path("toggle_save/<int:post_id>/", views.toggle_save, name="toggle_save"),
    path("update_post_status/<int:post_id>/", views.update_post_status, name="update_post_status"),
    path("reader_dashboard/", views.reader_dashboard, name="reader_dashboard"),
    path("author_dashboard/", views.author_dashboard, name="author_dashboard"),
    path("author_management/", views.author_management, name="author_management"),
    path("dashboard/", views.dashboard_redirect, name="dashboard_redirect"),
]
