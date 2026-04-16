from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib import messages
from django.db.models import Count
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import rotate_token
from django.http import HttpResponse
from django.utils.translation import gettext as _
from .forms import UserRegisterForm, ProfileUpdateForm, AddressForm
from orders.models import Order
from .models import Profile, Address


@csrf_exempt
def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            rotate_token(request)
            from cart.views import _merge_session_to_db

            _merge_session_to_db(request)
            messages.success(
                request, _("Welcome back! You have been logged in successfully.")
            )
            next_url = request.GET.get("next")
            return redirect(next_url if next_url else "home")
        else:
            messages.error(request, _("Invalid username or password."))
    else:
        form = AuthenticationForm()
    return render(request, "users/login.html", {"form": form})


@csrf_exempt
def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(
                request,
                _("Account created successfully! Please complete your profile."),
            )

            from .tasks import send_welcome_email_task

            send_welcome_email_task.delay(user.id)

            return redirect("profile")
        else:
            messages.error(request, _("Please fix the errors below."))
    else:
        form = UserRegisterForm()
    return render(request, "users/register.html", {"form": form})


@login_required
def profile(request):
    profile_obj, __ = Profile.objects.get_or_create(user=request.user)
    tab = request.GET.get("tab", "personal")

    if tab == "personal" and request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile_obj)
        if form.is_valid():
            form.save()
            u = request.user
            u.first_name = form.cleaned_data.get("first_name", "")
            u.last_name = form.cleaned_data.get("last_name", "")
            u.save()

            if request.headers.get("Hx-Request"):
                return HttpResponse(_("Profile updated successfully!"))
            messages.success(request, _("Profile updated successfully!"))
            return redirect("profile")
        else:
            messages.error(request, _("Please fix the errors below."))
    else:
        form = ProfileUpdateForm(
            instance=profile_obj,
            initial={
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
            },
        )

    password_form = PasswordChangeForm(request.user)

    context = {
        "profile_obj": profile_obj,
        "order_count": Order.objects.filter(user=request.user).count(),
        "wishlist_count": request.user.profile.wishlist.count(),
        "review_count": request.user.profile.reviews.count(),
        "address_count": Address.objects.filter(user=request.user).count(),
        "form": form,
        "password_form": password_form,
        "active_tab": tab,
        "orders": Order.objects.filter(user=request.user).order_by("-created_at"),
        "addresses": Address.objects.filter(user=request.user).order_by(
            "-is_default", "-created_at"
        ),
        "wishlist_items": request.user.profile.wishlist.select_related(
            "product", "product__brand"
        ).all(),
    }

    return render(request, "users/dashboard.html", context)


def checkout(request):
    return render(request, "users/checkout.html")


@login_required
def address_list(request):
    addresses = Address.objects.filter(user=request.user).order_by(
        "-is_default", "-created_at"
    )
    return render(request, "users/address_list.html", {"addresses": addresses})


@login_required
def address_add(request):
    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            if address.is_default:
                Address.objects.filter(user=request.user).update(is_default=False)
            address.save()
            messages.success(request, _("Address added successfully!"))

            if request.headers.get("Hx-Request"):
                addresses = Address.objects.filter(user=request.user).order_by(
                    "-is_default", "-created_at"
                )
                return render(
                    request, "users/dashboard/_addresses.html", {"addresses": addresses}
                )

            return redirect("users:address_list")
        else:
            messages.error(request, _("Please fix the errors below."))
    else:
        form = AddressForm()
    return render(request, "users/address_form.html", {"form": form, "action": "add"})


@login_required
def address_edit(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == "POST":
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            if form.cleaned_data.get("is_default"):
                Address.objects.filter(user=request.user).exclude(pk=pk).update(
                    is_default=False
                )
            form.save()
            messages.success(request, _("Address updated successfully!"))

            if request.headers.get("Hx-Request"):
                addresses = Address.objects.filter(user=request.user).order_by(
                    "-is_default", "-created_at"
                )
                return render(
                    request, "users/dashboard/_addresses.html", {"addresses": addresses}
                )

            return redirect("users:address_list")
        else:
            messages.error(request, _("Please fix the errors below."))
    else:
        form = AddressForm(instance=address)
    return render(request, "users/address_form.html", {"form": form, "action": "edit"})


@login_required
def address_delete(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    address.delete()
    messages.success(request, _("Address deleted successfully!"))

    if request.headers.get("Hx-Request"):
        addresses = Address.objects.filter(user=request.user).order_by(
            "-is_default", "-created_at"
        )
        return render(
            request, "users/dashboard/_addresses.html", {"addresses": addresses}
        )

    return redirect("users:address_list")


@login_required
def address_set_default(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    Address.objects.filter(user=request.user).update(is_default=False)
    address.is_default = True
    address.save()
    messages.success(request, _("Default address updated!"))

    if request.headers.get("Hx-Request"):
        addresses = Address.objects.filter(user=request.user).order_by(
            "-is_default", "-created_at"
        )
        return render(
            request, "users/dashboard/_addresses.html", {"addresses": addresses}
        )

    return redirect("users:address_list")


@login_required
def address_form_partial(request):
    address_id = request.GET.get("id")

    if address_id and address_id != "null":
        try:
            address = Address.objects.get(pk=int(address_id), user=request.user)
            form = AddressForm(instance=address)
            address_id = address.pk
        except Address.DoesNotExist:
            form = AddressForm()
            address_id = None
    else:
        form = AddressForm()
        address_id = None

    return render(
        request,
        "users/dashboard/_address_form_modal.html",
        {"form": form, "address_id": address_id},
    )


@login_required
def profile_order_detail(request, order_id):
    from orders.models import Order, OrderItem

    order = get_object_or_404(Order, id=order_id, user=request.user)
    items = order.items.select_related("product__brand").all()

    return render(
        request,
        "users/dashboard/_order_detail_drawer.html",
        {
            "order": order,
            "items": items,
        },
    )


@login_required
def password_change_partial(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Password changed successfully!"))

            if request.headers.get("Hx-Request"):
                return render(
                    request,
                    "users/dashboard/_security.html",
                    {
                        "password_form": PasswordChangeForm(request.user),
                        "user": request.user,
                    },
                )
            return redirect("users:password_change_done")
        else:
            if request.headers.get("Hx-Request"):
                return render(
                    request,
                    "users/dashboard/_security.html",
                    {
                        "password_form": form,
                        "user": request.user,
                    },
                )
    else:
        form = PasswordChangeForm(request.user)

    return render(
        request,
        "users/dashboard/_security.html",
        {
            "password_form": form,
            "user": request.user,
        },
    )
