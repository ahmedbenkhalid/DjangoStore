import asyncio
from asgiref.sync import sync_to_async
from django.core.cache import cache
from django.shortcuts import render
from django.db.models import Count
from django.utils.http import url_has_allowed_host_and_scheme
from products.models import Category, Product
from .models import Banner
from django.urls import translate_url
from django.http import HttpResponseRedirect
from django.conf import settings


def set_language_custom(request):
    """
    Smarter and safer language switcher.
    Handles both GET and POST, redirects to translated URL, and prevents open redirects.
    """
    if request.method == "POST":
        next_url = request.POST.get("next") or request.GET.get("next") or "/"
        lang_code = request.POST.get("language")
    else:
        next_url = request.GET.get("next", "/")
        lang_code = request.GET.get("language")

    # Security: Ensure next_url is local
    from django.utils.http import url_has_allowed_host_and_scheme
    if not url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        next_url = "/"

    if lang_code and lang_code in dict(settings.LANGUAGES):
        # 1. Force activate language in current thread
        from django.utils import translation
        translation.activate(lang_code)

        # 2. Translate the URL
        translated_url = translate_url(next_url, lang_code)
        
        # Fallback if translate_url didn't change the prefix or failed
        if not translated_url or translated_url == next_url:
            import re
            # Remove existing language prefix if any (e.g., /en/ or /ar/)
            path_no_lang = re.sub(r'^/(en|ar)/', '/', next_url)
            # Ensure we don't have double slashes
            path_no_lang = '/' + path_no_lang.lstrip('/')
            translated_url = f"/{lang_code}{path_no_lang}"

        response = HttpResponseRedirect(translated_url)

        # 3. Persist preference in session and cookie
        if hasattr(request, "session"):
            request.session[settings.LANGUAGE_COOKIE_NAME] = lang_code
        
        response.set_cookie(
            settings.LANGUAGE_COOKIE_NAME,
            lang_code,
            max_age=settings.LANGUAGE_COOKIE_AGE,
            path="/",
            samesite="Lax",
        )
        return response

    return HttpResponseRedirect(next_url)


def home(request):
    categories = cache.get("home_categories")
    if categories is None:
        # Get top 4 categories by product count for better homepage relevancy
        categories = list(
            Category.objects.annotate(product_count=Count("products")).order_by(
                "-product_count"
            )[:4]
        )
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
                "discount_price",
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
                "discount_price",
                "brand__id",
                "brand__name",
            )
            .all()[:8]
        )
        cache.set("most_liked_products", most_liked, 1800)

    # Banners
    banners = cache.get("home_banners")
    # If here is no Caching make caching
    if banners is None:
        banners = list(Banner.objects.filter(is_active=True))
        cache.set("home_banners", banners, 3600)

    # Products on Sale
    sale_products = cache.get("sale_products")
    if sale_products is None:
        from django.db.models import F
        sale_products = list(
            Product.objects.filter(discount_price__lt=F("price"))
            .select_related("brand")
            .only(
                "id",
                "name",
                "slug",
                "img",
                "img_link",
                "price",
                "discount_price",
                "brand__id",
                "brand__name",
            )
            .order_by("-updated_at")[:8]
        )
        cache.set("sale_products", sale_products, 3600)

    context = {
        "categories": categories,
        "featured_products": featured_products,
        "most_liked_products": most_liked,
        "banners": banners,
        "sale_products": sale_products,
    }
    return render(request, "home.html", context)
