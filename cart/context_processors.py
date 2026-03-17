from products.models import Product


def cart(request):
    """
    Make cart items, total and count available globally for the offcanvas panel.

    Performance notes:
    - Skips the DB entirely when the session cart is empty (no cart key or
      all values are 0) — so static pages like Home/About pay zero cost.
    - Uses a single IN-query + select_related so there is NO N+1.
    """
    raw_cart = request.session.get("cart", {})

    # Skip DB hit entirely if cart is empty
    if not raw_cart:
        return {"cart_items": [], "cart_total": 0, "cart_count": 0}

    cart_count = sum(raw_cart.values())
    if cart_count == 0:
        return {"cart_items": [], "cart_total": 0, "cart_count": 0}

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

    return {"cart_items": items, "cart_total": total, "cart_count": actual_count}
