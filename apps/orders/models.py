from django.db import models
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.contrib.auth.models import User
from products.models import Product


class OrderStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    CONFIRMED = "confirmed", "Confirmed"
    PROCESSING = "processing", "Processing"
    SHIPPED = "shipped", "Shipped"
    DELIVERED = "delivered", "Delivered"
    CANCELLED = "cancelled", "Cancelled"
    REFUNDED = "refunded", "Refunded"


class PaymentMethod(models.TextChoices):
    CASH_ON_DELIVERY = "cash_on_delivery", "Cash on Delivery"


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PAID = "paid", "Paid"


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    status = models.CharField(
        max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH_ON_DELIVERY,
    )
    payment_status = models.CharField(
        max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_address = models.TextField()
    phone = models.CharField(max_length=20)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        indexes = [
            # most common query: all orders for a user, sorted by newest
            models.Index(fields=["user", "-created_at"], name="order_user_created_idx"),
            models.Index(fields=["status"], name="order_status_idx"),
            models.Index(fields=["payment_method"], name="order_pay_method_idx"),
            models.Index(fields=["payment_status"], name="order_pay_status_idx"),
        ]

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"

    def calculate_total(self):
        """
        Compute total from OrderItems using a single aggregate query.
        Uses F() expressions — no Python-level N+1.
        """
        result = self.items.aggregate(
            total=Sum(
                ExpressionWrapper(
                    F("quantity") * F("price"),
                    output_field=DecimalField(max_digits=10, decimal_places=2),
                )
            )
        )
        total = result["total"] or 0
        self.total_amount = total
        self.save(update_fields=["total_amount"])
        return total

    @property
    def total(self):
        """
        Return stored total_amount if available (avoids extra DB hit).
        Falls back to calculate_total() only when amount is genuinely missing.
        """
        if self.total_amount:
            return self.total_amount
        return self.calculate_total()


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="order_items"
    )
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"
        indexes = [
            models.Index(fields=["order"], name="orderitem_order_idx"),
            models.Index(fields=["product"], name="orderitem_product_idx"),
        ]

    def __str__(self):
        return f"{self.quantity}x {self.product.name} in Order #{self.order.id}"

    @property
    def subtotal(self):
        # price is stored on the item — no extra DB hit
        return self.quantity * self.price
