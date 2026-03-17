from django.contrib import admin

from .models import Category, Brand, Tag, Product, Review, Wishlist


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    list_editable = ("slug",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    actions = ["delete_selected"]

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            actions["delete_selected"] = (
                actions["delete_selected"][0],
                "delete_selected",
                "Delete selected categories",
            )
        return actions


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    list_editable = ("slug",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    actions = ["delete_selected"]

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            actions["delete_selected"] = (
                actions["delete_selected"][0],
                "delete_selected",
                "Delete selected brands",
            )
        return actions


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    list_editable = ("slug",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    actions = ["delete_selected"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "price", "stock", "category", "brand", "created_at")
    list_editable = ("price", "stock", "sku")
    list_filter = ("category", "brand", "tags", "created_at")
    search_fields = ("name", "description", "sku")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")
    filter_horizontal = ("tags",)
    fieldsets = (
        ("Basic Information", {"fields": ("name", "slug", "sku", "description")}),
        ("Pricing & Inventory", {"fields": ("price", "stock", "type")}),
        ("Organization", {"fields": ("category", "brand", "tags")}),
        ("Links & Media", {"fields": ("external_link", "img", "img_link")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
    actions = ["delete_selected"]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("product__name", "user__user__username", "comment")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__user__username", "product__name")
