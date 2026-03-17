import re
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Profile, Address


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label=_("Email address"),
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": _("Email address")}
        ),
    )
    username = forms.CharField(
        label=_("Username"),
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Username")}
        ),
    )
    password1 = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": _("Password")}
        ),
    )
    password2 = forms.CharField(
        label=_("Confirm password"),
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": _("Confirm password")}
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "username" in self.fields:
            self.fields["username"].help_text = None
        if "password1" in self.fields:
            self.fields["password1"].help_text = None

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["username", "email"]

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not email:
            raise ValidationError(_("Email is required."))

        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError(_("Please enter a valid email address."))

        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(_("An account with this email already exists."))

        return email.lower()

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if username:
            if len(username) < 3:
                raise ValidationError(_("Username must be at least 3 characters long."))
            if not re.match(r"^[a-zA-Z0-9_]+$", username):
                raise ValidationError(
                    _("Username can only contain letters, numbers, and underscores.")
                )
        return username

    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")
        if password1:
            if len(password1) < 8:
                raise ValidationError(_("Password must be at least 8 characters long."))
            if not re.search(r"[A-Z]", password1):
                raise ValidationError(
                    _("Password must contain at least one uppercase letter.")
                )
            if not re.search(r"[a-z]", password1):
                raise ValidationError(
                    _("Password must contain at least one lowercase letter.")
                )
            if not re.search(r"[0-9]", password1):
                raise ValidationError(_("Password must contain at least one number."))
        return password1

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise ValidationError(_("Passwords do not match."))

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class ProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(
        label=_("First Name"),
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("First Name")}
        ),
        required=False,
    )
    last_name = forms.CharField(
        label=_("Last Name"),
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Last Name")}
        ),
        required=False,
    )
    phone = forms.CharField(
        label=_("Phone Number"),
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Phone Number")}
        ),
        required=False,
    )
    address = forms.CharField(
        label=_("Shipping Address"),
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "placeholder": _("Shipping Address"),
                "rows": 3,
            }
        ),
        required=False,
    )

    class Meta:
        model = Profile
        fields = ["first_name", "last_name", "phone", "address", "avatar"]


class AddressForm(forms.ModelForm):
    name = forms.CharField(
        label=_("Address Name"),
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Home, Work, etc.")}
        ),
    )
    phone = forms.CharField(
        label=_("Phone Number"),
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Phone Number")}
        ),
    )
    address = forms.CharField(
        label=_("Address"),
        widget=forms.Textarea(
            attrs={"class": "form-control", "placeholder": _("Full address"), "rows": 2}
        ),
    )
    city = forms.CharField(
        label=_("City"),
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("City")}
        ),
    )
    area = forms.CharField(
        label=_("Area/District"),
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Area/District (Optional)"),
            }
        ),
        required=False,
    )
    is_default = forms.BooleanField(
        label=_("Set as default address"),
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        required=False,
    )

    class Meta:
        model = Address
        fields = ["name", "phone", "address", "city", "area", "is_default"]
