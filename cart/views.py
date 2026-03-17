from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.template.loader import render_to_string

from products.models import Product


def get_cart(request):
    return request.session.get("cart", {})


def save_cart(request, cart):
    request.session["cart"] = cart
    request.session.modified = True


def _build_cart_context(request):
    """
    Build cart context dict.

    Single IN-query with select_related — no N+1 queries.
    Skips the DB entirely when the cart is empty.
    """
    cart = get_cart(request)

    if not cart:
        return {"cart_items": [], "cart_total": 0, "cart_count": 0}

    cart_count = sum(cart.values())
    product_ids = [int(pid) for pid in cart]

    # One query only
    product_dict = {
        p.id: p
        for p in Product.objects.filter(id__in=product_ids).select_related("brand")
    }

    items = []
    total = 0
    for pid_str, quantity in cart.items():
        product = product_dict.get(int(pid_str))
        if product and quantity > 0:
            subtotal = product.price * quantity
            total += subtotal
            items.append(
                {"product": product, "quantity": quantity, "subtotal": subtotal}
            )

    return {"cart_items": items, "cart_total": total, "cart_count": cart_count}


def cart_detail(request):
    """Shopping cart page."""
    ctx = _build_cart_context(request)
    ctx["products"] = ctx["cart_items"]
    ctx["total"] = ctx["cart_total"]
    return render(request, "cart/cart_detail.html", ctx)


def cart_add(request, product_id):
    """Add (or decrement) a product in the cart."""
    # Validate product exists first — only one query, no product object needed
    if not Product.objects.filter(id=product_id).exists():
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {"success": False, "error": "Product not found"}, status=404
            )
        return redirect("cart:detail")

    cart = get_cart(request)

    try:
        quantity = int(request.POST.get("quantity", 1))
    except TypeError, ValueError:
        quantity = 1

    pid = str(product_id)
    if pid in cart:
        cart[pid] = max(0, cart[pid] + quantity)
        if cart[pid] == 0:
            del cart[pid]
    elif quantity > 0:
        cart[pid] = quantity

    save_cart(request, cart)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"success": True, "cart_count": sum(cart.values())})

    messages.success(request, "Cart updated.")
    return redirect("cart:detail")


def cart_remove(request, product_id):
    """Remove a product from the cart (no DB query needed)."""
    cart = get_cart(request)
    pid = str(product_id)

    if pid in cart:
        del cart[pid]
        save_cart(request, cart)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"success": True, "cart_count": sum(cart.values())})

    messages.success(request, "Item removed from cart.")
    return redirect("cart:detail")


def offcanvas_fragment(request):
    """Return rendered cart partials as JSON for the AJAX offcanvas refresher."""
    ctx = _build_cart_context(request)
    items_html = render_to_string("components/cart_items.html", ctx, request=request)
    footer_html = render_to_string("components/cart_footer.html", ctx, request=request)
    return JsonResponse(
        {
            "items_html": items_html,
            "footer_html": footer_html,
            "cart_count": ctx["cart_count"],
        }
    )
