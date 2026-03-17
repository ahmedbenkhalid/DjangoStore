from django.contrib import admin
from .models import Order, OrderItem, OrderStatus, PaymentStatus


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "quantity", "price", "subtotal")
    fields = ("product", "quantity", "price", "subtotal")

    def subtotal(self, obj):
        return obj.subtotal if obj else 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "status",
        "payment_method",
        "payment_status",
        "total_amount",
        "created_at",
    )
    list_display_links = ("id", "user")
    list_editable = ("status", "payment_status")
    list_filter = ("status", "payment_method", "payment_status", "created_at")
    search_fields = ("id", "user__username", "user__email", "shipping_address")
    readonly_fields = ("total_amount", "created_at", "updated_at")
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Order Information",
            {"fields": ("id", "user", "status", "payment_method", "payment_status")},
        ),
        ("Customer Details", {"fields": ("shipping_address", "phone", "notes")}),
        ("Financial", {"fields": ("total_amount",), "classes": ("collapse",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    inlines = [OrderItemInline]

    actions = [
        "mark_as_confirmed",
        "mark_as_processing",
        "mark_as_shipped",
        "mark_as_delivered",
        "mark_as_cancelled",
        "mark_payment_as_paid",
    ]

    @admin.action(description="Mark selected orders as Confirmed")
    def mark_as_confirmed(self, request, queryset):
        updated = queryset.update(status=OrderStatus.CONFIRMED)
        self.message_user(request, f"{updated} orders marked as Confirmed.")

    @admin.action(description="Mark selected orders as Processing")
    def mark_as_processing(self, request, queryset):
        updated = queryset.update(status=OrderStatus.PROCESSING)
        self.message_user(request, f"{updated} orders marked as Processing.")

    @admin.action(description="Mark selected orders as Shipped")
    def mark_as_shipped(self, request, queryset):
        updated = queryset.update(status=OrderStatus.SHIPPED)
        self.message_user(request, f"{updated} orders marked as Shipped.")

    @admin.action(description="Mark selected orders as Delivered")
    def mark_as_delivered(self, request, queryset):
        updated = queryset.update(status=OrderStatus.DELIVERED)
        self.message_user(request, f"{updated} orders marked as Delivered.")

    @admin.action(description="Mark selected orders as Cancelled")
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status=OrderStatus.CANCELLED)
        self.message_user(request, f"{updated} orders marked as Cancelled.")

    @admin.action(description="Mark payment as Paid")
    def mark_payment_as_paid(self, request, queryset):
        updated = queryset.update(payment_status=PaymentStatus.PAID)
        self.message_user(request, f"{updated} orders marked as Paid.")


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "product", "quantity", "price", "subtotal")
    list_filter = ("order__status", "product__category")
    search_fields = ("order__id", "product__name")
    readonly_fields = ("subtotal",)

    def subtotal(self, obj):
        return obj.subtotal
