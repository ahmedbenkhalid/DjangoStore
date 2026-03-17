from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.core.cache import cache
from django.core.paginator import Paginator

from products.models import Product, Category, Wishlist, Review
from products.forms import ReviewForm


# ── helpers ───────────────────────────────────────────────────────────────────


def _get_cached_categories():
    """Return all categories, cached for 1 hour."""
    cats = cache.get("all_categories")
    if cats is None:
        cats = list(Category.objects.only("id", "name", "slug"))
        cache.set("all_categories", cats, 3600)
    return cats


# ── views ─────────────────────────────────────────────────────────────────────


def product_list(request):
    """Products page with filtering, sorting, and pagination."""

    # JSON autocomplete — minimal fields, no prefetch needed
    query = request.GET.get("q")
    if request.GET.get("format") == "json":
        qs = Product.objects.only("id", "name", "slug", "price", "img")
        if query:
            qs = qs.filter(name__icontains=query)
        return JsonResponse(
            {"products": list(qs[:10].values("id", "name", "slug", "price", "img"))}
        )

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
    )

    # Filters
    category_slug = request.GET.get("category")
    if category_slug:
        products = products.filter(category__slug=category_slug)

    if query:
        products = products.filter(name__icontains=query)

    # Sort
    sort = request.GET.get("sort", "-created_at")
    if sort in ("price", "-price", "name", "-name", "created_at", "-created_at"):
        products = products.order_by(sort)

    # Pagination — Paginator only hits the DB slice, not the full table
    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    context = {
        "page_obj": page_obj,
        "categories": _get_cached_categories(),
        "current_category": category_slug,
        "current_sort": sort,
        "query": query,
    }

    if request.headers.get("HX-Target") == "product-grid":
        return render(request, "products/partials/product_grid.html", context)

    return render(request, "pages/products/products.html", context)


def product_detail(request, slug):
    """Product detail page with caching."""
    cache_key = f"product_detail_{slug}"
    p_data = cache.get(cache_key)

    if p_data is None:
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
        p_data = {
            "product": product,
            "related_products": related_products,
            "avg_rating": round(avg_rating, 1),
            "review_count": product.reviews.count(),
        }
        cache.set(cache_key, p_data, 60 * 30)

    # Reviews are fetched fresh (no cache for now to show updates immediately)
    reviews = p_data["product"].reviews.select_related("user__user").all()

    is_in_wishlist = False
    user_review = None
    if request.user.is_authenticated:
        is_in_wishlist = Wishlist.objects.filter(
            user=request.user.profile, product_id=p_data["product"].id
        ).exists()
        user_review = reviews.filter(user=request.user.profile).first()

    ctx = {
        **p_data,
        "reviews": reviews,
        "is_in_wishlist": is_in_wishlist,
        "user_review": user_review,
        "review_form": ReviewForm(),
    }
    return render(request, "pages/products/products_details.html", ctx)


@login_required
@require_POST
def add_review(request, product_id):
    """Add or update a product review."""
    product = get_object_or_404(Product, id=product_id)
    form = ReviewForm(request.POST)

    if form.is_valid():
        review, created = Review.objects.update_or_create(
            product=product,
            user=request.user.profile,
            defaults={
                "rating": form.cleaned_data["rating"],
                "comment": form.cleaned_data["comment"],
            },
        )
        # Clear product detail cache to refresh potential average rating displays elsewhere
        cache.delete(f"product_detail_{product.slug}")

    return redirect(product.get_absolute_url())


def category_list(request):
    """Categories listing page."""
    context = {"categories": _get_cached_categories()}

    if request.headers.get("HX-Target") == "category-grid":
        return render(request, "pages/category/partials/category_grid.html", context)

    return render(request, "pages/category/category_list.html", context)


def category_detail(request, slug):
    """Category detail page — category cached per slug for 10 minutes."""
    from django.core.cache import cache

    cache_key = f"category_{slug}"
    category = cache.get(cache_key)
    if category is None:
        category = get_object_or_404(
            Category.objects.only("id", "name", "slug", "image"), slug=slug
        )
        cache.set(cache_key, category, 60 * 10)

    products = category.products.select_related("brand").only(
        "id", "name", "slug", "img", "img_link", "price", "brand__id", "brand__name"
    )

    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    context = {"category": category, "page_obj": page_obj}

    if request.headers.get("HX-Target") == "category-products":
        return render(request, "pages/category/partials/category_products.html", context)

    return render(request, "pages/category/category_detail.html", context)


@login_required
def wishlist_list(request):
    """List products in user's wishlist."""
    wishlist_items = (
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
    return render(
        request, "pages/products/wishlist.html", {"wishlist_items": wishlist_items}
    )


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

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        from .models import Wishlist as WL

        count = WL.objects.filter(user=request.user.profile).count()
        return JsonResponse(
            {"status": "success", "action": action, "wishlist_count": count}
        )

    return redirect(product.get_absolute_url())
