from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django.core.cache import cache
from asgiref.sync import sync_to_async

from products.models import Product
from cart.models import Cart, CartItem


def _get_session_cart(request):
    return request.session.get("cart", {})


def _save_session_cart(request, cart):
    request.session["cart"] = cart
    request.session.modified = True
    _invalidate_cart_cache(request)


def _get_db_cart(request):
    if not request.user.is_authenticated:
        return None
    cart, _ = Cart.objects.get_or_create(user=request.user)
    return cart


def _merge_session_to_db(request):
    """Merge session cart into DB cart on login."""
    if not request.user.is_authenticated:
        return
    session_cart = _get_session_cart(request)
    if not session_cart:
        return
    db_cart = _get_db_cart(request)
    product_ids = [int(pid) for pid in session_cart.keys()]
    products = {p.id: p for p in Product.objects.filter(id__in=product_ids)}
    for pid_str, qty in session_cart.items():
        product = products.get(int(pid_str))
        if product and qty > 0:
            CartItem.objects.update_or_create(
                cart=db_cart, product=product, defaults={"quantity": qty}
            )
    request.session.pop("cart", None)


def _sync_db_to_session(request):
    """Sync DB cart to session for context processor compatibility."""
    if not request.user.is_authenticated:
        return _get_session_cart(request)
    db_cart = _get_db_cart(request)
    if not db_cart:
        return _get_session_cart(request)
    items = db_cart.items.select_related("product").all()
    cart = {str(item.product_id): item.quantity for item in items if item.quantity > 0}
    request.session["cart"] = cart
    request.session.modified = True
    return cart


def get_cart(request):
    if request.user.is_authenticated:
        return _sync_db_to_session(request)
    return _get_session_cart(request)


def save_cart(request, cart):
    if request.user.is_authenticated:
        db_cart = _get_db_cart(request)
        current_items = {ci.product_id: ci for ci in db_cart.items.all()}
        for pid_str, qty in cart.items():
            product_id = int(pid_str)
            if qty <= 0:
                if product_id in current_items:
                    current_items[product_id].delete()
            elif product_id in current_items:
                current_items[product_id].quantity = qty
                current_items[product_id].save(update_fields=["quantity"])
            else:
                CartItem.objects.create(
                    cart=db_cart, product_id=product_id, quantity=qty
                )
        removed = set(current_items.keys()) - {int(k) for k in cart.keys()}
        if removed:
            db_cart.items.filter(product_id__in=removed).delete()
    _save_session_cart(request, cart)
    _invalidate_cart_cache(request)


def _invalidate_cart_cache(request):
    session_key = request.session.session_key or "anon"
    cache.delete(f"cart_ctx_{session_key}")


async def _build_cart_context(request):
    cart = await sync_to_async(get_cart)(request)

    if not cart:
        return {"cart_items": [], "cart_total": 0, "cart_count": 0}

    cart_count = sum(cart.values())
    product_ids = [int(pid) for pid in cart]

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
    ctx = await _build_cart_context(request)
    ctx["products"] = ctx["cart_items"]
    ctx["total"] = ctx["cart_total"]
    return await sync_to_async(render)(request, "cart/cart_detail.html", ctx)


async def _build_cart_response(request, cart):
    ctx = await _build_cart_context(request)
    items_html = await sync_to_async(render_to_string)(
        "shared/partials/cart_items.html", ctx, request=request
    )
    footer_html = await sync_to_async(render_to_string)(
        "shared/partials/cart_footer.html", ctx, request=request
    )
    return JsonResponse(
        {
            "success": True,
            "cart_count": ctx["cart_count"],
            "items_html": items_html,
            "footer_html": footer_html,
        }
    )


async def cart_add(request, product_id):
    product = await sync_to_async(get_object_or_404)(Product, id=product_id)
    cart = await sync_to_async(get_cart)(request)

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 1

    pid = str(product_id)
    current_qty = cart.get(pid, 0)
    new_qty = max(0, current_qty + quantity)

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

    await sync_to_async(save_cart)(request, cart)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return await _build_cart_response(request, cart)

    messages.success(request, _("Cart updated."))
    return redirect("cart:detail")


async def cart_remove(request, product_id):
    cart = await sync_to_async(get_cart)(request)
    pid = str(product_id)

    if pid in cart:
        del cart[pid]
        await sync_to_async(save_cart)(request, cart)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return await _build_cart_response(request, cart)

    messages.success(request, _("Item removed from cart."))
    return redirect("cart:detail")


async def offcanvas_fragment(request):
    ctx = await _build_cart_context(request)
    items_html = await sync_to_async(render_to_string)(
        "shared/partials/cart_items.html", ctx, request=request
    )
    footer_html = await sync_to_async(render_to_string)(
        "shared/partials/cart_footer.html", ctx, request=request
    )
    return JsonResponse(
        {
            "items_html": items_html,
            "footer_html": footer_html,
            "cart_count": ctx["cart_count"],
        }
    )
