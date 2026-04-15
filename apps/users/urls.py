from django.urls import path, reverse_lazy
from . import views
from django.contrib.auth import views as auth_views

app_name = "users"

urlpatterns = [
    path("auth/register/", views.register, name="register"),
    path("auth/login/", views.login_view, name="login"),
    path("auth/logout/", auth_views.LogoutView.as_view(next_page="/"), name="logout"),
    path("auth/profile/", views.profile, name="profile"),
    path("auth/profile/update/", views.profile, name="profile_update"),
    path(
        "auth/password-change/",
        auth_views.PasswordChangeView.as_view(
            template_name="pages/users/password_change.html",
            success_url=reverse_lazy("users:password_change_done"),
        ),
        name="password_change",
    ),
    path(
        "auth/password-change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="pages/users/password_change_done.html"
        ),
        name="password_change_done",
    ),
    path(
        "profile/order/<int:order_id>/",
        views.profile_order_detail,
        name="profile_order_detail",
    ),
    path(
        "profile/address/form/", views.address_form_partial, name="address_form_partial"
    ),
    path("addresses/", views.address_list, name="address_list"),
    path("addresses/add/", views.address_add, name="address_add"),
    path("addresses/<int:pk>/edit/", views.address_edit, name="address_edit"),
    path("addresses/<int:pk>/delete/", views.address_delete, name="address_delete"),
    path(
        "addresses/<int:pk>/set-default/",
        views.address_set_default,
        name="address_set_default",
    ),
]
