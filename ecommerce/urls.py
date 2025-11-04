from django.urls import path
from . import views

app_name = 'ecommerce'

urlpatterns = [
    path('products/', views.product_list, name='product_list'),
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('checkout/', views.checkout, name='checkout'),
    path('inventory/', views.inventory_dashboard, name='inventory_dashboard'),
    path('inventory/add/', views.add_product, name='add_product'),
    path('inventory/delete/<int:product_id>/', views.delete_product, name='delete_product'),
]
