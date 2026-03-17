from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import gettext_lazy as _
from .forms import UserRegisterForm, ProfileUpdateForm, AddressForm
from orders.models import Order
from .models import Profile, Address


@csrf_exempt
def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(
                request, _("Welcome back! You have been logged in successfully.")
            )
            next_url = request.GET.get("next")
            return redirect(next_url if next_url else "home")
        else:
            messages.error(request, _("Invalid username or password."))
    else:
        form = AuthenticationForm()
    return render(request, "pages/users/login.html", {"form": form})


@csrf_exempt
def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request,
                _("Account created successfully! Please complete your profile."),
            )
            return redirect("profile")
        else:
            messages.error(request, _("Please fix the errors below."))
    else:
        form = UserRegisterForm()
    return render(request, "pages/users/register.html", {"form": form})


@login_required
def profile(request):
    profile_obj, _ = Profile.objects.get_or_create(user=request.user)
    recent_orders = (
        Order.objects.filter(user=request.user)
        .prefetch_related("items__product")
        .order_by("-created_at")[:5]
    )

    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile_obj)
        if form.is_valid():
            form.save()
            request.user.first_name = form.cleaned_data.get("first_name", "")
            request.user.last_name = form.cleaned_data.get("last_name", "")
            request.user.save()
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
        "pages/users/profile.html",
        {
            "profile_obj": profile_obj,
            "recent_orders": recent_orders,
            "form": form,
        },
    )


@csrf_exempt
def checkout(request):
    return render(request, "pages/users/checkout.html")


@login_required
def address_list(request):
    addresses = Address.objects.filter(user=request.user).order_by(
        "-is_default", "-created_at"
    )
    return render(request, "pages/users/address_list.html", {"addresses": addresses})


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
    return render(
        request, "pages/users/address_form.html", {"form": form, "action": "add"}
    )


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
    return render(
        request, "pages/users/address_form.html", {"form": form, "action": "edit"}
    )


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
