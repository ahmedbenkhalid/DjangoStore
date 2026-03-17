from django.contrib import admin

from .models import Cart, CartItem


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("user",)

    fieldsets = (
        ("Cart Information", {"fields": ("id", "user")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("id", "cart", "product", "quantity", "subtotal", "created_at")
    list_filter = ("created_at",)
    search_fields = ("cart__user__username", "product__name")
    readonly_fields = ("created_at", "updated_at")

    def subtotal(self, obj):
        return obj.subtotal

    subtotal.short_description = "Subtotal"
