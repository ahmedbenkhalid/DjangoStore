from django.contrib import admin
from django.utils.html import format_html
from .models import Banner


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ["get_preview", "title", "order", "is_active"]
    list_display_links = ["get_preview", "title"]
    list_editable = ["order", "is_active"]
    ordering = ["order"]
    search_fields = ["title", "subtitle", "title_ar", "subtitle_ar"]
    
    fieldsets = (
        ("General Information", {
            "fields": ("title", "title_ar", "subtitle", "subtitle_ar", "order", "is_active")
        }),
        ("Desktop Media", {
            "fields": ("image", "image_link")
        }),
        ("Mobile Media", {
            "fields": ("image_mobile", "image_mobile_link")
        }),
        ("Link / Action", {
            "fields": ("link", "link_text", "link_text_ar")
        }),
    )

    def get_preview(self, obj):
        img_url = ""
        if obj.image:
            img_url = obj.image.url
        elif obj.image_link:
            img_url = obj.image_link
            
        if img_url:
            return format_html('<img src="{}" style="width: 100px; height: auto; border-radius: 4px;" />', img_url)
        return "No Image"
    
    get_preview.short_description = "Preview"
