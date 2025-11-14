import json
import uuid
from decimal import Decimal

from django.core.paginator import Paginator
from django.utils.text import slugify

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import NoReverseMatch, reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import ProductForm
from .models import Cart, CartItem, Order, OrderItem, Payment, Product
from .utils import normalize_product_filters

try:
    import razorpay
except ImportError:
    razorpay = None


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


def _get_checkout_flow():
    return getattr(settings, 'ECOMMERCE_CHECKOUT_FLOW', 'normal').lower()


def _prepare_razorpay_checkout(request, cart, grand_total):
    if razorpay is None:
        return False, {'error_message': 'Razorpay SDK is not installed. Add `razorpay` to requirements.'}

    key_id = getattr(settings, 'RAZORPAY_KEY_ID', '').strip()
    key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '').strip()
    currency = getattr(settings, 'RAZORPAY_CURRENCY', 'INR').upper()

    if not key_id or not key_secret:
        return False, {'error_message': 'Razorpay credentials are missing. Configure RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET.'}

    try:
        amount_paise = int((grand_total * Decimal('100')).quantize(Decimal('1')))
    except Exception:
        return False, {'error_message': 'Unable to calculate Razorpay order amount.'}

    session_order = request.session.get('razorpay_order')
    if (
        session_order
        and session_order.get('cart_id') == cart.id
        and session_order.get('amount') == amount_paise
    ):
        order = {
            'id': session_order.get('order_id'),
            'amount': session_order.get('amount'),
            'currency': session_order.get('currency', currency),
        }
    else:
        receipt = f"cart-{cart.id or 'guest'}-{uuid.uuid4().hex[:6]}"

        client = razorpay.Client(auth=(key_id, key_secret))
        try:
            order = client.order.create(
                data={
                    'amount': amount_paise,
                    'currency': currency,
                    'receipt': receipt,
                    'payment_capture': 1,
                    'notes': {
                        'cart_id': str(cart.id or ''),
                        'user_id': str(request.user.id),
                    },
                }
            )
        except Exception as exc:
            return False, {'error_message': f'Unable to create Razorpay order: {exc}'}

        request.session['razorpay_order'] = {
            'order_id': order.get('id'),
            'amount': order.get('amount'),
            'currency': order.get('currency'),
            'cart_id': cart.id,
        }
        request.session.modified = True

    prefill_name = request.user.get_full_name() or request.user.get_username()

    return True, {
        'razorpay_key_id': key_id,
        'razorpay_order': order,
        'razorpay_currency': currency,
        'razorpay_prefill': {
            'name': prefill_name,
            'email': request.user.email,
        },
        'razorpay_callback_url': reverse('ecommerce:razorpay_callback'),
    }


def _create_order_from_cart(cart, cart_context, status='paid'):
    order = Order.objects.create(
        user=cart.user,
        total_amount=cart_context['grand_total'],
        status=status,
    )
    for item in cart_context['items']:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.unit_price,
        )
    cart.items.all().delete()
    return order


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
    filters = normalize_product_filters(request.GET)

    base_queryset = Product.objects.all().with_actual_downloads()
    products_qs = base_queryset.apply_catalog_filters(filters)

    paginator = Paginator(products_qs, filters['per_page'])
    page_obj = paginator.get_page(filters['page'])
    products = page_obj.object_list

    category_values = (
        base_queryset.filter(is_active=True)
        .exclude(category__isnull=True)
        .exclude(category__exact='')
        .values_list('category', flat=True)
        .order_by('category')
        .distinct()
    )

    category_options = []
    category_label_map = {}
    for category in category_values:
        slug = slugify(category)
        category_options.append({'slug': slug, 'label': category})
        category_label_map[slug] = category

    applied_filters = []
    if filters['search']:
        applied_filters.append({'label': 'Search', 'value': filters['search']})

    for slug in filters['categories']:
        display = category_label_map.get(slug, slug.replace('-', ' ').title())
        applied_filters.append({'label': 'Category', 'value': display})

    if filters['is_free'] is True:
        applied_filters.append({'label': 'Pricing', 'value': 'Free only'})
    elif filters['is_free'] is False:
        applied_filters.append({'label': 'Pricing', 'value': 'Paid only'})

    if filters['price_min'] is not None:
        applied_filters.append({'label': 'Min price', 'value': f"₹{filters['price_min']}"})

    if filters['price_max'] is not None:
        applied_filters.append({'label': 'Max price', 'value': f"₹{filters['price_max']}"})

    if filters['sort'] != 'newest':
        sort_labels = {
            'oldest': 'Oldest first',
            'price_asc': 'Price: low to high',
            'price_desc': 'Price: high to low',
            'popular': 'Most popular',
        }
        applied_filters.append({'label': 'Sort', 'value': sort_labels.get(filters['sort'], filters['sort'].title())})

    query_without_page = request.GET.copy()
    if 'page' in query_without_page:
        query_without_page.pop('page')
    base_querystring = query_without_page.urlencode()

    context = {
        'filters': filters,
        'products': products,
        'page_obj': page_obj,
        'paginator': paginator,
        'category_options': category_options,
        'applied_filters': applied_filters,
        'per_page_choices': [12, 24, 36, 48],
        'base_querystring': base_querystring,
        'clear_filters_url': request.path,
        'request': request,
    }

    template_name = 'ecommerce/product_list.html'
    if request.headers.get('HX-Request'):
        template_name = 'ecommerce/partials/product_grid.html'

    return render(request, template_name, context)

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
    flow = _get_checkout_flow()
    context['checkout_flow'] = flow

    template_name = 'ecommerce/checkout.html'

    if flow == 'razorpay':
        if context['grand_total'] <= Decimal('0.00'):
            messages.info(request, 'Cart total is zero; using standard checkout instead of Razorpay.')
        else:
            ready, razorpay_context = _prepare_razorpay_checkout(request, cart, context['grand_total'])
            if ready:
                context.update(razorpay_context)
                template_name = 'ecommerce/razorpay_checkout.html'
            else:
                error_message = razorpay_context.get('error_message')
                if error_message:
                    messages.error(request, error_message)

    return render(request, template_name, context)


@login_required
@require_POST
def razorpay_callback(request):
    if _get_checkout_flow() != 'razorpay':
        return HttpResponseBadRequest('Razorpay checkout is disabled.')

    if razorpay is None:
        return HttpResponseBadRequest('Razorpay SDK is not installed on the server.')

    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid payload.')

    order_id = payload.get('razorpay_order_id')
    payment_id = payload.get('razorpay_payment_id')
    signature = payload.get('razorpay_signature')

    if not all([order_id, payment_id, signature]):
        return HttpResponseBadRequest('Missing payment confirmation fields.')

    session_order = request.session.get('razorpay_order') or {}
    if session_order.get('order_id') != order_id:
        return HttpResponseBadRequest('Checkout session expired. Please try again.')

    key_id = getattr(settings, 'RAZORPAY_KEY_ID', '').strip()
    key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '').strip()
    if not key_id or not key_secret:
        return HttpResponseBadRequest('Razorpay credentials are not configured.')

    client = razorpay.Client(auth=(key_id, key_secret))
    try:
        client.utility.verify_payment_signature(
            {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature,
            }
        )
    except Exception:
        return HttpResponseBadRequest('Payment signature verification failed.')

    cart = Cart.objects.filter(user=request.user).first()
    if not cart or not cart.items.exists():
        return HttpResponseBadRequest('Cart is empty. No order was created.')

    cart_context = _build_cart_context(cart)
    order = _create_order_from_cart(cart, cart_context, status='paid')

    Payment.objects.create(
        order=order,
        payment_id=payment_id,
        amount=cart_context['grand_total'],
        status='captured',
        payment_method='razorpay',
    )

    request.session.pop('razorpay_order', None)
    request.session['last_completed_order_id'] = order.id
    request.session.modified = True

    return JsonResponse({'status': 'success', 'redirect_url': reverse('ecommerce:checkout_success')})


@login_required
def checkout_success(request):
    order_id = request.session.pop('last_completed_order_id', None)
    if not order_id:
        messages.info(request, 'No recent order to display.')
        return redirect('ecommerce:checkout')

    order = (
        Order.objects.filter(pk=order_id, user=request.user)
        .select_related('user')
        .prefetch_related('items__product')
        .first()
    )

    if not order:
        messages.error(request, 'Order could not be found.')
        return redirect('ecommerce:checkout')

    try:
        payment = order.payment
    except Payment.DoesNotExist:
        payment = None

    return render(
        request,
        'ecommerce/checkout_success.html',
        {
            'order': order,
            'payment': payment,
        },
    )

# Delete product
@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
@require_POST
def delete_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    product.delete()
    messages.success(request, 'Product deleted successfully.')
    return redirect(_resolve_next(request, 'ecommerce:inventory_dashboard'))