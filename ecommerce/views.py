from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import NoReverseMatch, reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import ProductForm
from .models import Cart, CartItem, Order, OrderItem, Payment, Product


def _resolve_next(request, default_route='author_management'):
    """Determine a safe URL to redirect back to after actions."""
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return next_url

    try:
        return reverse(default_route)
    except NoReverseMatch:
        try:
            return reverse('ecommerce:inventory_dashboard')
        except NoReverseMatch:
            return '/'


def _build_cart_context(cart):
    """Prepare reusable context data for cart-based views."""
    items = list(cart.items.select_related('product'))
    subtotal = Decimal('0.00')

    for item in items:
        if item.quantity != 1:
            item.quantity = 1
            item.save(update_fields=['quantity'])
        item.is_free = getattr(item.product, 'is_free', False)
        item.original_price = item.product.price
        item.discount_price = item.product.discount_price
        if item.is_free:
            unit_price = Decimal('0.00')
        else:
            if item.discount_price is not None:
                unit_price = item.discount_price
            else:
                unit_price = item.product.price or Decimal('0.00')
        line_total = unit_price * item.quantity
        item.unit_price = unit_price
        item.line_total = line_total
        subtotal += line_total

    return {
        'cart': cart,
        'items': items,
        'total_items': len(items),
        'subtotal': subtotal,
        'grand_total': subtotal,
    }


@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def inventory_dashboard(request):
    products = Product.objects.all()
    return render(request, 'ecommerce/inventory_dashboard.html', {'products': products})


@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product added successfully.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.replace('_', ' ').title()}: {error}")
        return redirect(_resolve_next(request, 'ecommerce:inventory_dashboard'))

    form = ProductForm()
    return render(request, 'ecommerce/add_product.html', {'form': form})


@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def edit_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)

    if request.method != 'POST':
        return redirect(_resolve_next(request, 'ecommerce:inventory_dashboard'))

    form = ProductForm(request.POST, request.FILES, instance=product)
    if form.is_valid():
        form.save()
        messages.success(request, 'Product updated successfully.')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field.replace('_', ' ').title()}: {error}")

    return redirect(_resolve_next(request, 'ecommerce:inventory_dashboard'))


# Product listing

def product_list(request):
    products = Product.objects.all().order_by('-created_at')
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
    if cart_item.quantity != 1:
        cart_item.quantity = 1
        cart_item.save(update_fields=['quantity'])
    messages.success(request, 'Product added to cart.')
    return redirect('ecommerce:cart_detail')


@login_required
def buy_now(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if cart_item.quantity != 1:
        cart_item.quantity = 1
        cart_item.save(update_fields=['quantity'])
    messages.success(request, 'Product ready for checkout.')
    return redirect('ecommerce:checkout')


@login_required
def remove_from_cart(request, item_id):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item = get_object_or_404(CartItem, pk=item_id, cart=cart)
    cart_item.delete()
    messages.info(request, 'Item removed from cart.')
    return redirect('ecommerce:cart_detail')

# Cart detail
@login_required
def cart_detail(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    context = _build_cart_context(cart)
    return render(request, 'ecommerce/cart_detail.html', context)

# Checkout
@login_required
def checkout(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    context = _build_cart_context(cart)
    # Payment gateway integration goes here
    # On successful payment, create Order and Payment records
    return render(request, 'ecommerce/checkout.html', context)

# Delete product
@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
@require_POST
def delete_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    product.delete()
    messages.success(request, 'Product deleted successfully.')
    return redirect(_resolve_next(request, 'ecommerce:inventory_dashboard'))