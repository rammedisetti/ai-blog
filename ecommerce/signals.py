from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Order


@receiver(post_save, sender=Order)
def increment_product_downloads(sender, instance, created, **kwargs):
    """
    Increment downloads_count for each product when an order transitions to 'paid' or 'completed'.
    Only increments once per order using a flag to avoid duplicate signals.
    """
    if instance.status in ('paid', 'completed'):
        # Check if we've already processed this order to avoid double-counting
        if not hasattr(instance, '_downloads_incremented'):
            for order_item in instance.items.select_related('product'):
                order_item.product.downloads_count = F('downloads_count') + order_item.quantity
                order_item.product.save(update_fields=['downloads_count'])
            
            # Mark this order as processed to prevent re-incrementing on subsequent saves
            instance._downloads_incremented = True
