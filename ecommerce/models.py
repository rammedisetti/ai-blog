from typing import Any, Dict

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Count, DecimalField, Q
from django.db.models.functions import Coalesce
from django.utils.text import slugify

User = get_user_model()


class ProductQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def with_effective_price(self):
        return self.annotate(
            effective_price=Coalesce('discount_price', 'price', output_field=DecimalField(max_digits=10, decimal_places=2))
        )

    def with_actual_downloads(self):
        """Annotate products with actual download count from completed orders."""
        return self.annotate(
            actual_downloads=Count(
                'orderitem',
                filter=Q(orderitem__order__status__in=['paid', 'completed']),
                distinct=True
            )
        )

    def apply_catalog_filters(self, filters: Dict[str, Any]):
        filters = filters or {}
        qs = self

        only_active = filters.get('only_active')
        if only_active or only_active is None:
            qs = qs.filter(is_active=True)

        categories = filters.get('categories') or []
        if categories:
            category_query = Q()
            for slug in categories:
                normalized = slug.replace('-', ' ').strip()
                category_query |= Q(category__iexact=slug)
                category_query |= Q(category__iexact=normalized)
            qs = qs.filter(category_query)

        is_free = filters.get('is_free')
        if is_free is True:
            qs = qs.filter(is_free=True)
        elif is_free is False:
            qs = qs.filter(is_free=False)

        search = filters.get('search')
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(description__icontains=search)
                | Q(tags__icontains=search)
            )

        needs_price_annotation = any(
            filters.get(key) is not None for key in ('price_min', 'price_max')
        ) or filters.get('sort') in {'price_asc', 'price_desc'}

        if needs_price_annotation:
            qs = qs.with_effective_price()

        price_min = filters.get('price_min')
        if price_min is not None:
            qs = qs.filter(effective_price__gte=price_min)

        price_max = filters.get('price_max')
        if price_max is not None:
            qs = qs.filter(effective_price__lte=price_max)

        sort = filters.get('sort', 'newest')
        if sort == 'newest':
            qs = qs.order_by('-created_at')
        elif sort == 'oldest':
            qs = qs.order_by('created_at')
        elif sort == 'price_asc':
            qs = qs.order_by('effective_price', 'created_at')
        elif sort == 'price_desc':
            qs = qs.order_by('-effective_price', '-created_at')
        elif sort == 'popular':
            qs = qs.order_by('-downloads_count', '-created_at')

        return qs


class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    category = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    file_url = models.URLField(max_length=500)
    thumbnail = models.ImageField(upload_to='product_thumbnails/')
    is_free = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    downloads_count = models.PositiveIntegerField(default=0)
    tags = models.CharField(max_length=255, blank=True)

    objects = ProductQuerySet.as_manager()

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            unique_slug = base_slug or slugify(f"product-{self.product_id or ''}")
            counter = 1
            while Product.objects.filter(slug=unique_slug).exclude(pk=self.pk).exists():
                unique_slug = f"{base_slug}-{counter}" if base_slug else f"product-{counter}"
                counter += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        indexes = [
            models.Index(fields=['is_active', 'created_at'], name='product_active_created_idx'),
            models.Index(fields=['is_free', 'price'], name='product_free_price_idx'),
            models.Index(fields=['downloads_count'], name='product_downloads_idx'),
            models.Index(fields=['category'], name='product_category_idx'),
        ]

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, default='pending')

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50)
    payment_method = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    # Integrate payment gateway here (e.g., Stripe, Razorpay, PayPal)
    # Store gateway response or transaction details as needed
