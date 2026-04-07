from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db.models import Count
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import rotate_token
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

    recent_orders = list(
        Order.objects.filter(user=request.user)
        .prefetch_related("items__product__brand")
        .order_by("-created_at")[:5]
    )

    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile_obj)
        if form.is_valid():
            form.save()
            u = request.user
            u.first_name = form.cleaned_data.get("first_name", "")
            u.last_name = form.cleaned_data.get("last_name", "")
            u.save()
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

    return render(
        request,
        "users/profile.html",
        {
            "profile_obj": profile_obj,
            "recent_orders": recent_orders,
            "order_count": Order.objects.filter(user=request.user).count(),
            "wishlist_count": request.user.profile.wishlist.count(),
            "review_count": request.user.profile.reviews.count(),
            "address_count": Address.objects.filter(user=request.user).count(),
            "form": form,
        },
    )


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
    return redirect("users:address_list")


@login_required
def address_set_default(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    Address.objects.filter(user=request.user).update(is_default=False)
    address.is_default = True
    address.save()
    messages.success(request, _("Default address updated!"))
    return redirect("users:address_list")
