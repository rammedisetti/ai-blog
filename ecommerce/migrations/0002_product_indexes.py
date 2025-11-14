from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ecommerce", "0001_initial"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="product",
            index=models.Index(fields=["is_active", "created_at"], name="product_active_created_idx"),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(fields=["is_free", "price"], name="product_free_price_idx"),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(fields=["downloads_count"], name="product_downloads_idx"),
        ),
        migrations.AddIndex(
            model_name="product",
            index=models.Index(fields=["category"], name="product_category_idx"),
        ),
    ]
