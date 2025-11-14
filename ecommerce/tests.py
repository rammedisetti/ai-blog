from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import QueryDict
from django.test import TestCase

from .models import Product
from .utils import normalize_product_filters


class ProductFilterNormalizationTests(TestCase):
    def test_normalize_product_filters_clamps_and_defaults(self):
        params = QueryDict(mutable=True)
        params.setlist("category", ["tech", "accessories"])
        params["is_free"] = "false"
        params["price_min"] = "10.5"
        params["price_max"] = "invalid"
        params["sort"] = "popular"
        params["per_page"] = "120"
        params["page"] = "0"
        params["q"] = "wireless"

        filters = normalize_product_filters(params)

        self.assertEqual(filters["categories"], ["tech", "accessories"])
        self.assertFalse(filters["is_free"])
        self.assertEqual(filters["price_min"], Decimal("10.5"))
        self.assertIsNone(filters["price_max"])
        self.assertEqual(filters["sort"], "popular")
        self.assertEqual(filters["per_page"], 48)
        self.assertEqual(filters["page"], 1)
        self.assertEqual(filters["search"], "wireless")
        self.assertTrue(filters["only_active"])


class ProductQuerySetFilterTests(TestCase):
    def setUp(self):
        self.free_product = Product.objects.create(
            name="Free Guide",
            description="Comprehensive free resource",
            category="Tech Accessories",
            price=0,
            discount_price=None,
            file_url="https://example.com/free-guide.pdf",
            thumbnail=SimpleUploadedFile("thumb1.jpg", b"filecontent", content_type="image/jpeg"),
            is_free=True,
            downloads_count=150,
            tags="guide,free",
        )
        self.discount_product = Product.objects.create(
            name="Premium Toolkit",
            description="Includes components and resources",
            category="Tech Accessories",
            price=1200,
            discount_price=900,
            file_url="https://example.com/toolkit.zip",
            thumbnail=SimpleUploadedFile("thumb2.jpg", b"filecontent", content_type="image/jpeg"),
            is_free=False,
            downloads_count=250,
            tags="toolkit,premium",
        )
        self.audio_product = Product.objects.create(
            name="Audio Course",
            description="Audio focused content",
            category="Audio Gear",
            price=500,
            discount_price=None,
            file_url="https://example.com/audio-course.mp3",
            thumbnail=SimpleUploadedFile("thumb3.jpg", b"filecontent", content_type="image/jpeg"),
            is_free=False,
            downloads_count=50,
            tags="audio,course",
        )

    def test_apply_catalog_filters_category_and_pricing(self):
        params = QueryDict("category=tech-accessories&is_free=false&sort=price_desc")
        filters = normalize_product_filters(params)

        qs = Product.objects.apply_catalog_filters(filters)
        self.assertEqual(list(qs), [self.discount_product])

    def test_apply_catalog_filters_price_range_and_search(self):
        params = QueryDict("price_min=400&price_max=950&sort=price_asc&q=course")
        filters = normalize_product_filters(params)

        qs = Product.objects.apply_catalog_filters(filters)
        self.assertEqual(list(qs), [self.audio_product])

    def test_apply_catalog_filters_popularity_sort(self):
        params = QueryDict("sort=popular")
        filters = normalize_product_filters(params)

        qs = Product.objects.apply_catalog_filters(filters)
        self.assertEqual(list(qs), [self.discount_product, self.free_product, self.audio_product])