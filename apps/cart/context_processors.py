from django.core.cache import cache

from products.models import Product


def cart(request):
    """
    Make cart items, total and count available globally for the offcanvas panel.
    Uses Django cache to avoid re-fetching products on every request.
    Cache is invalidated by cart_add/cart_remove views.
    """
    raw_cart = request.session.get("cart", {})

    # Skip DB hit entirely if cart is empty
    if not raw_cart:
        return {"cart_items": [], "cart_total": 0, "cart_count": 0}

    cart_count = sum(raw_cart.values())
    if cart_count == 0:
        return {"cart_items": [], "cart_total": 0, "cart_count": 0}

    # Build a fingerprint of the cart to use as cache key
    cart_key = "|".join(f"{k}:{v}" for k, v in sorted(raw_cart.items()))
    session_key = request.session.session_key or "anon"
    cache_key = f"cart_ctx_{session_key}"

    # Check if cached cart matches current cart fingerprint
    cached = cache.get(cache_key)
    if cached and cached.get("key") == cart_key:
        return cached["data"]

    # Single query — no N+1
    product_ids = [int(pid) for pid in raw_cart]
    product_dict = {
        p.id: p
        for p in Product.objects.filter(id__in=product_ids).select_related("brand")
    }

    items = []
    total = 0
    actual_count = 0
    for pid_str, quantity in raw_cart.items():
        product = product_dict.get(int(pid_str))
        if product and quantity > 0:
            subtotal = product.price * quantity
            total += subtotal
            actual_count += quantity
            items.append(
                {"product": product, "quantity": quantity, "subtotal": subtotal}
            )

    result = {"cart_items": items, "cart_total": total, "cart_count": actual_count}

    # Cache for 60 seconds (invalidated by cart views on change)
    cache.set(cache_key, {"key": cart_key, "data": result}, 60)

    return result
