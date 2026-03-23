from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from asgiref.sync import sync_to_async

from products.models import Product


def get_cart(request):
    return request.session.get("cart", {})


def save_cart(request, cart):
    request.session["cart"] = cart
    request.session.modified = True


async def _build_cart_context(request):
    """
    Build cart context dict.
    Single IN-query with select_related — no N+1 queries.
    Skips the DB entirely when the cart is empty.
    """
    cart = await sync_to_async(get_cart)(request)

    if not cart:
        return {"cart_items": [], "cart_total": 0, "cart_count": 0}

    cart_count = sum(cart.values())
    product_ids = [int(pid) for pid in cart]

    # Evaluate product list asynchronously
    products = [
        p
        async for p in Product.objects.filter(id__in=product_ids).select_related(
            "brand"
        )
    ]
    product_dict = {p.id: p for p in products}

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


async def cart_detail(request):
    """Shopping cart page."""
    ctx = await _build_cart_context(request)
    ctx["products"] = ctx["cart_items"]
    ctx["total"] = ctx["cart_total"]
    # render is synchronous, need sync_to_async
    return await sync_to_async(render)(request, "pages/cart/cart_detail.html", ctx)


@sync_to_async
def cart_add(request, product_id):
    """Add (or decrement) a product in the cart with stock validation."""
    product = get_object_or_404(Product, id=product_id)
    cart = get_cart(request)

    try:
        quantity = int(request.POST.get("quantity", 1))
    except TypeError, ValueError:
        quantity = 1

    pid = str(product_id)
    current_qty = cart.get(pid, 0)
    new_qty = max(0, current_qty + quantity)

    # Validate stock (only if increasing)
    if quantity > 0 and new_qty > product.stock:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "success": False,
                    "error": _("Only %(stock)s items left in stock.")
                    % {"stock": product.stock},
                },
                status=400,
            )
        messages.error(
            request,
            _("Sorry, only %(stock)s items are available for %(name)s.")
            % {"stock": product.stock, "name": product.name},
        )
        return redirect("cart:detail")

    if new_qty == 0:
        if pid in cart:
            del cart[pid]
    else:
        cart[pid] = new_qty

    save_cart(request, cart)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"success": True, "cart_count": sum(cart.values())})

    messages.success(request, _("Cart updated."))
    return redirect("cart:detail")


@sync_to_async
def cart_remove(request, product_id):
    """Remove a product from the cart (Sync wrapped)."""
    cart = get_cart(request)
    pid = str(product_id)

    if pid in cart:
        del cart[pid]
        save_cart(request, cart)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"success": True, "cart_count": sum(cart.values())})

    messages.success(request, _("Item removed from cart."))
    return redirect("cart:detail")


async def offcanvas_fragment(request):
    """Return rendered cart partials as JSON for the AJAX offcanvas refresher."""
    ctx = await _build_cart_context(request)
    items_html = await sync_to_async(render_to_string)(
        "components/cart_items.html", ctx, request=request
    )
    footer_html = await sync_to_async(render_to_string)(
        "components/cart_footer.html", ctx, request=request
    )
    return JsonResponse(
        {
            "items_html": items_html,
            "footer_html": footer_html,
            "cart_count": ctx["cart_count"],
        }
    )
