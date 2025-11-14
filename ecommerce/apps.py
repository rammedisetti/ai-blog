from django.apps import AppConfig


class EcommerceConfig(AppConfig):
    name = 'ecommerce'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        import ecommerce.signals  # noqa
