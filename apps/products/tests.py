from decimal import Decimal
from django.test import TestCase
from products.models import Product, Category, Brand


class DiscountPercentTestCase(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Test Category", slug="test-category"
        )
        self.brand = Brand.objects.create(name="Test Brand", slug="test-brand")

    def test_discount_percent_zero_price(self):
        product = Product.objects.create(
            name="Test Product",
            slug="test-product-zero",
            price=Decimal("0.00"),
            discount_price=Decimal("5.00"),
            category=self.category,
            brand=self.brand,
        )
        self.assertEqual(product.discount_percent, 0)

    def test_discount_percent_negative_price(self):
        product = Product.objects.create(
            name="Test Product",
            slug="test-product-negative",
            price=Decimal("-10.00"),
            discount_price=Decimal("5.00"),
            category=self.category,
            brand=self.brand,
        )
        self.assertEqual(product.discount_percent, 0)

    def test_discount_percent_positive_price(self):
        product = Product.objects.create(
            name="Test Product",
            slug="test-product-positive",
            price=Decimal("100.00"),
            discount_price=Decimal("75.00"),
            category=self.category,
            brand=self.brand,
        )
        self.assertEqual(product.discount_percent, 25)

    def test_discount_percent_no_discount(self):
        product = Product.objects.create(
            name="Test Product",
            slug="test-product-no-discount",
            price=Decimal("100.00"),
            category=self.category,
            brand=self.brand,
        )
        self.assertEqual(product.discount_percent, 0)

    def test_discount_percent_full_discount(self):
        product = Product.objects.create(
            name="Test Product",
            slug="test-product-full-discount",
            price=Decimal("100.00"),
            discount_price=Decimal("0.00"),
            category=self.category,
            brand=self.brand,
        )
        self.assertEqual(product.discount_percent, 100)

    def test_discount_percent_small_discount(self):
        product = Product.objects.create(
            name="Test Product",
            slug="test-product-small-discount",
            price=Decimal("99.99"),
            discount_price=Decimal("66.66"),
            category=self.category,
            brand=self.brand,
        )
        self.assertEqual(product.discount_percent, 33)
