from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from products.models import Product
from orders.models import Order, OrderItem, OrderStatus, PaymentMethod, PaymentStatus


def get_cart(request):
    """Get cart from session."""
    return request.session.get("cart", {})


def save_cart(request, cart):
    """Save cart to session."""
    request.session["cart"] = cart
    request.session.modified = True


def get_cart_products(request):
    """
    Get cart products with quantities and totals.
    Single IN-query with select_related — no N+1.
    """
    cart = get_cart(request)
    if not cart:
        return [], 0

    product_ids = [int(pid) for pid in cart]
    product_dict = {
        p.id: p
        for p in Product.objects.filter(id__in=product_ids)
        .select_related("brand")
        .only(
            "id", "name", "slug", "img", "img_link", "price", "brand__id", "brand__name"
        )
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

    return items, total


@login_required
def checkout(request):
    """Checkout page — display cart items and shipping form."""
    products, total = get_cart_products(request)

    if not products:
        messages.error(request, "Your cart is empty.")
        return redirect("cart:detail")

    from users.models import Address

    addresses = Address.objects.filter(user=request.user).order_by(
        "-is_default", "-created_at"
    )
    default_address = addresses.filter(is_default=True).first()

    default_phone = default_address.phone if default_address else ""
    default_shipping = ""
    if default_address:
        default_shipping = (
            f"{default_address.address}, {default_address.area}, {default_address.city}"
            if default_address.area
            else f"{default_address.address}, {default_address.city}"
        )

    return render(
        request,
        "orders/checkout.html",
        {
            "products": products,
            "total": total,
            "default_phone": default_phone,
            "default_address": default_shipping,
            "addresses": addresses,
        },
    )


@login_required
def create_order(request):
    """Create order from cart."""
    if request.method != "POST":
        return redirect("orders:checkout")

    products, total = get_cart_products(request)

    if not products:
        messages.error(request, "Your cart is empty.")
        return redirect("cart:detail")

    shipping_address = request.POST.get("shipping_address", "").strip()
    phone = request.POST.get("phone", "").strip()
    notes = request.POST.get("notes", "").strip()

    if not shipping_address or not phone:
        messages.error(request, "Please provide shipping address and phone number.")
        return redirect("orders:checkout")

    order = Order.objects.create(
        user=request.user,
        status=OrderStatus.PENDING,
        payment_method=PaymentMethod.CASH_ON_DELIVERY,
        payment_status=PaymentStatus.PENDING,
        total_amount=total,
        shipping_address=shipping_address,
        phone=phone,
        notes=notes if notes else None,
    )

    # Bulk-create all order items in one query instead of one per item
    OrderItem.objects.bulk_create(
        [
            OrderItem(
                order=order,
                product=item["product"],
                quantity=item["quantity"],
                price=item["product"].price,
            )
            for item in products
        ]
    )

    save_cart(request, {})
    return redirect("orders:confirmation", order_id=order.id)


@login_required
def order_confirmation(request, order_id):
    """Order confirmation page."""
    order = get_object_or_404(
        Order.objects.prefetch_related("items__product__brand"),
        id=order_id,
        user=request.user,
    )
    return render(
        request,
        "orders/order_confirmation.html",
        {
            "order": order,
            "items": order.items.all(),  # uses the already-prefetched cache
        },
    )


@login_required
def order_list(request):
    """User's order history."""
    orders = (
        Order.objects.filter(user=request.user)
        .prefetch_related("items__product")
        .only("id", "status", "total_amount", "created_at", "payment_status")
    )
    return render(request, "orders/order_list.html", {"orders": orders})


@login_required
def order_detail(request, order_id):
    """Order detail page — prefetch items + product in one query."""
    order = get_object_or_404(
        Order.objects.prefetch_related("items__product__brand"),
        id=order_id,
        user=request.user,
    )
    return render(
        request,
        "orders/order_detail.html",
        {
            "order": order,
            "items": order.items.all(),  # uses the already-prefetched cache
        },
    )
