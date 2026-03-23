from django.core.cache import cache
from django.shortcuts import render
from django.db.models import Count

from products.models import Category, Product
from .models import Banner


def home(request):
    categories = cache.get("home_categories")
    if categories is None:
        categories = list(Category.objects.all()[:4])
        cache.set("home_categories", categories, 3600)

    # Featured Products (newest)
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

    most_liked = cache.get("most_liked_products")
    if most_liked is None:
        most_liked = list(
            Product.objects.select_related("brand")
            .annotate(wishlist_count=Count("wishlist"))
            .filter(wishlist_count__gt=0)
            .order_by("-wishlist_count")
            .only(
                "id",
                "name",
                "slug",
                "img",
                "img_link",
                "price",
                "brand__id",
                "brand__name",
            )[:8]
        )
        cache.set("most_liked_products", most_liked, 1800)

    # Banners
    banners = cache.get("home_banners")
    if banners is None:
        banners = list(Banner.objects.filter(is_active=True))
        cache.set("home_banners", banners, 3600)

    context = {
        "categories": categories,
        "featured_products": featured_products,
        "most_liked_products": most_liked,
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
