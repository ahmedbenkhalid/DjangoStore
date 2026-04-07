from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from products.models import Product


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="cart")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user.username}"

    def get_total(self):
        """
        Single aggregate query — no N+1, no per-item Python loop.
        Uses F() expressions so multiplication happens in the DB.
        """
        result = self.items.aggregate(
            total=Sum(
                ExpressionWrapper(
                    F("quantity") * F("product__price"),
                    output_field=DecimalField(max_digits=10, decimal_places=2),
                )
            )
        )
        return result["total"] or 0

    @property
    def total(self):
        return self.get_total()


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="cart_items"
    )
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("cart", "product")
        indexes = [
            models.Index(fields=["cart"], name="cartitem_cart_idx"),
            models.Index(fields=["product"], name="cartitem_product_idx"),
        ]

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    @property
    def subtotal(self):
        """
        Requires product to be pre-fetched with select_related('product')
        on the queryset — no extra DB hit when done correctly.
        """
        return self.product.price * self.quantity
