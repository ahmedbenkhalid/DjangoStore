from asgiref.sync import sync_to_async
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.core.cache import cache
from django.core.paginator import Paginator
from django.contrib import messages
from django.utils.translation import gettext as _

from products.models import Product, Category, Wishlist, Review
from products.forms import ReviewForm


# ── helpers ───────────────────────────────────────────────────────────────────


async def _get_cached_categories():
    """Return all categories, cached for 1 hour."""
    cats = await cache.aget("all_categories")
    if cats is None:
        cats = [c async for c in Category.objects.only("id", "name", "slug")]
        await cache.aset("all_categories", cats, 3600)
    return cats


# ── views ─────────────────────────────────────────────────────────────────────


async def product_list(request):
    """Products page with filtering, sorting, and pagination."""

    query = request.GET.get("q")
    if request.GET.get("format") == "json":
        qs = Product.objects.only("id", "name", "slug", "price", "img")
        if query and len(query) <= 200:
            qs = qs.filter(name__icontains=query)
        result = [p async for p in qs[:10].values("id", "name", "slug", "price", "img")]
        return JsonResponse({"products": result})

    if query and len(query) > 200:
        query = query[:200]

    # Full queryset — single DB round-trip per page via Paginator
    products = Product.objects.select_related("category", "brand").only(
        "id",
        "name",
        "slug",
        "img",
        "img_link",
        "price",
        "category__id",
        "category__slug",
        "brand__id",
        "brand__name",
        "stock",
        "discount_price",
    )

    # Filters
    category_slug = request.GET.get("category")
    if category_slug:
        products = products.filter(category__slug=category_slug)

    on_sale = request.GET.get("on_sale")
    if on_sale == "true":
        from django.db.models import F
        products = products.filter(discount_price__lt=F("price"))

    if query:
        products = products.filter(name__icontains=query)

    # Brand filter
    selected_brands = request.GET.getlist("brand")
    if selected_brands:
        products = products.filter(brand__slug__in=selected_brands)

    # Price range filter
    price_min = request.GET.get("price_min")
    price_max = request.GET.get("price_max")
    if price_min:
        try:
            products = products.filter(price__gte=float(price_min))
        except ValueError:
            pass
    if price_max:
        try:
            products = products.filter(price__lte=float(price_max))
        except ValueError:
            pass

    # Stock filter
    in_stock = request.GET.get("in_stock")
    if in_stock:
        products = products.filter(stock__gt=0)

    # Sort
    sort = request.GET.get("sort", "-created_at")
    if sort in ("price", "-price", "name", "-name", "created_at", "-created_at"):
        products = products.order_by(sort)

    # Pagination — Paginator only hits the DB slice, not the full table
    paginator = Paginator(products, 12)

    def get_page_sync():
        p = paginator.get_page(request.GET.get("page", 1))
        # Evaluate object list
        __ = list(p.object_list)
        return p

    page_obj = await sync_to_async(get_page_sync)()

    # Get all brands for filter sidebar
    def get_brands():
        from products.models import Brand

        return list(Brand.objects.only("id", "name", "slug").order_by("name"))

    brands = await sync_to_async(get_brands)()

    context = {
        "page_obj": page_obj,
        "categories": await _get_cached_categories(),
        "brands": brands,
        "current_category": category_slug,
        "current_sort": sort,
        "query": query,
        "selected_brands": selected_brands,
        "price_min": price_min,
        "price_max": price_max,
        "in_stock": in_stock,
        "on_sale": on_sale,
    }

    if request.headers.get("X-Stock-Request") == "true":
        products = Product.objects.filter(
            id__in=[p.id for p in page_obj.object_list]
        ).only("id", "stock")
        stock_data = {
            str(p.id): "out_of_stock"
            if p.stock == 0
            else "low_stock"
            if p.stock <= 5
            else "in_stock"
            for p in products
        }
        return JsonResponse({"stock": stock_data})

    if request.headers.get("HX-Target") == "product-grid":
        return await sync_to_async(render)(
            request, "products/partials/product_grid.html", context
        )

    return await sync_to_async(render)(request, "products/products.html", context)


async def product_detail(request, slug):
    """Product detail page with caching."""
    cache_key = f"product_detail_{slug}"
    p_data = await cache.aget(cache_key)

    if p_data is None:

        def get_product_data():
            from django.db.models import Avg

            product = get_object_or_404(
                Product.objects.select_related("category", "brand").prefetch_related(
                    "tags"
                ),
                slug=slug,
            )
            related_products = list(
                Product.objects.filter(category_id=product.category_id)
                .exclude(id=product.id)
                .select_related("brand")
                .only(
                    "id",
                    "name",
                    "slug",
                    "img",
                    "img_link",
                    "price",
                    "brand__id",
                    "brand__name",
                )[:4]
            )
            avg_rating = product.reviews.aggregate(Avg("rating"))["rating__avg"] or 0
            return {
                "product": product,
                "related_products": related_products,
                "avg_rating": round(avg_rating, 1),
                "review_count": product.reviews.count(),
            }

        p_data = await sync_to_async(get_product_data)()
        await cache.aset(cache_key, p_data, 60 * 30)

    # Reviews fetched fresh with proper prefetch to avoid N+1
    def fetch_reviews():
        reviews = list(
            p_data["product"]
            .reviews.select_related("user", "user__user", "user__user__profile")
            .all()
        )
        is_in_wishlist = False
        user_review = None
        if request.user.is_authenticated:
            # Single query for wishlist check
            is_in_wishlist = Wishlist.objects.filter(
                user=request.user.profile, product_id=p_data["product"].id
            ).exists()
            # Find user's existing review
            user_review = next(
                (r for r in reviews if r.user_id == request.user.profile.id), None
            )
        return reviews, is_in_wishlist, user_review

    reviews, is_in_wishlist, user_review = await sync_to_async(fetch_reviews)()

    ctx = {
        **p_data,
        "reviews": reviews,
        "is_in_wishlist": is_in_wishlist,
        "user_review": user_review,
        "review_form": ReviewForm(),
    }
    return await sync_to_async(render)(request, "products/products_details.html", ctx)


@login_required
def add_review(request, product_id):
    """Add or update a product review."""
    from products.forms import ReviewForm as RF

    product = get_object_or_404(Product, id=product_id)

    rate_key = f"review_rate_{request.user.id}_{product_id}"
    if cache.get(rate_key):
        messages.error(
            request, _("Please wait a moment before submitting another review.")
        )
        return redirect(product.get_absolute_url())

    form = RF(request.POST)

    if form.is_valid():
        Review.objects.update_or_create(
            product=product,
            user=request.user.profile,
            defaults={
                "rating": form.cleaned_data["rating"],
                "comment": form.cleaned_data["comment"],
            },
        )
        cache.delete(f"product_detail_{product.slug}")
        cache.delete("all_products_reviews")
        cache.set(rate_key, True, 60)

    return redirect(product.get_absolute_url())


@login_required
@require_POST
def delete_review(request, review_id):
    """Delete a product review."""
    review = get_object_or_404(Review, id=review_id, user=request.user.profile)
    product_slug = review.product.slug
    review.delete()
    cache.delete(f"product_detail_{product_slug}")

    if request.headers.get("HX-Request") == "true":
        return JsonResponse({"status": "deleted", "review_id": review_id})

    return redirect(reverse("products:detail", kwargs={"slug": product_slug}))


async def category_list(request):
    """Categories listing page."""
    context = {"categories": await _get_cached_categories()}

    if request.headers.get("HX-Target") == "category-grid":
        return await sync_to_async(render)(
            request, "category/partials/category_grid.html", context
        )

    return await sync_to_async(render)(request, "category/category_list.html", context)


async def category_detail(request, slug):
    """Category detail page — category cached per slug for 10 minutes."""
    from django.core.cache import cache

    cache_key = f"category_{slug}"
    category = await cache.aget(cache_key)
    if category is None:

        def get_category():
            return get_object_or_404(
                Category.objects.only("id", "name", "slug", "image"), slug=slug
            )

        category = await sync_to_async(get_category)()
        await cache.aset(cache_key, category, 60 * 10)

    products = category.products.select_related("brand").only(
        "id", "name", "slug", "img", "img_link", "price", "brand__id", "brand__name"
    )

    paginator = Paginator(products, 12)

    def get_page_sync():
        p = paginator.get_page(request.GET.get("page", 1))
        __ = list(p.object_list)
        return p

    page_obj = await sync_to_async(get_page_sync)()

    context = {"category": category, "page_obj": page_obj}

    if request.headers.get("HX-Target") == "category-products":
        return await sync_to_async(render)(
            request, "category/partials/category_products.html", context
        )

    return await sync_to_async(render)(
        request, "category/category_detail.html", context
    )


@login_required
def wishlist_list(request):
    """List products in user's wishlist."""
    wishlist_items = list(
        Wishlist.objects.filter(user=request.user.profile)
        .select_related("product__brand")
        .only(
            "id",
            "product__id",
            "product__name",
            "product__slug",
            "product__img",
            "product__img_link",
            "product__price",
            "product__brand__id",
            "product__brand__name",
        )
    )
    return render(request, "products/wishlist.html", {"wishlist_items": wishlist_items})


@login_required
@require_POST
def toggle_wishlist(request, product_id):
    """Add or remove product from user's wishlist."""
    product = get_object_or_404(Product, id=product_id)
    wishlist_item, created = Wishlist.objects.get_or_create(
        user=request.user.profile, product=product
    )

    if not created:
        wishlist_item.delete()
        action = "removed"
    else:
        action = "added"

    # Invalidate cached wishlist count
    cache.delete(f"wishlist_count_{request.user.id}")

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        from .models import Wishlist as WL

        count = WL.objects.filter(user=request.user.profile).count()
        # Update cache with fresh count
        cache.set(f"wishlist_count_{request.user.id}", count, 300)
        return JsonResponse(
            {
                "status": "success",
                "action": action,
                "wishlist_count": count,
                "in_wishlist": action == "added",
            }
        )

    return redirect(product.get_absolute_url())


def stock_status(request, product_id):
    """HTMX endpoint for live stock status polling."""
    from django.utils.translation import gettext as _

    product = get_object_or_404(Product, id=product_id)
    stock = product.stock

    if stock == 0:
        html = f'<span class="absolute top-2 end-2 inline-flex items-center px-2 py-0.5 text-xs font-bold text-red-700 bg-red-100 rounded-md">{_("Out of stock")}</span>'
    elif stock <= 5:
        html = f'<span class="absolute top-2 end-2 inline-flex items-center px-2 py-0.5 text-xs font-bold text-amber-800 bg-amber-100 rounded-md">{_("Only")} {stock} {_("left")}</span>'
    else:
        html = ""

    return JsonResponse({"stock": stock, "html": html})
