from .forms import ProductForm
from django.contrib.auth.decorators import login_required
# Inventory dashboard (list products)
from django.contrib.auth.decorators import user_passes_test

@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def inventory_dashboard(request):
    products = Product.objects.all()
    return render(request, 'ecommerce/inventory_dashboard.html', {'products': products})

# Add product
@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('ecommerce:inventory_dashboard')
    else:
        form = ProductForm()
    return render(request, 'ecommerce/add_product.html', {'form': form})
from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Cart, CartItem, Order, OrderItem, Payment
from django.contrib.auth.decorators import login_required
from django.contrib import messages

# Product listing

def product_list(request):
    products = Product.objects.filter(is_active=True)
    return render(request, 'ecommerce/product_list.html', {'products': products})

# Product detail

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    return render(request, 'ecommerce/product_detail.html', {'product': product})

# Add to cart
@login_required

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    messages.success(request, 'Product added to cart.')
    return redirect('ecommerce:cart_detail')

# Cart detail
@login_required

def cart_detail(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related('product')
    return render(request, 'ecommerce/cart_detail.html', {'cart': cart, 'items': items})

# Checkout
@login_required

def checkout(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related('product')
    # Payment gateway integration goes here
    # On successful payment, create Order and Payment records
    return render(request, 'ecommerce/checkout.html', {'cart': cart, 'items': items})
