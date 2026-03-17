from django.core.cache import cache
from django.shortcuts import render

from products.models import Category, Product
from .models import Banner


def home(request):
    categories = cache.get("home_categories")
    if categories is None:
        categories = list(Category.objects.all()[:8])
        cache.set("home_categories", categories, 3600)

    featured_products = cache.get("featured_products")
    if featured_products is None:
        featured_products = list(
            Product.objects.select_related("brand")
            .only(
                "id",
                "name",
                "slug",
                "img",
                "img_link",
                "price",
                "brand__id",
                "brand__name",
            )
            .all()[:8]
        )
        cache.set("featured_products", featured_products, 3600)

    banners = cache.get("home_banners")
    if banners is None:
        banners = list(Banner.objects.filter(is_active=True))
        cache.set("home_banners", banners, 3600)

    context = {
        "categories": categories,
        "featured_products": featured_products,
        "banners": banners,
    }
    return render(request, "pages/home.html", context)


def about(request):
    context = {
        "title": "About",
        "description": "About Us",
        "keywords": "About Us",
        "author": "About Us",
    }
    return render(request, "pages/about/about.html", context)
