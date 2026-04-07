from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

from core import views
from products import urls as products_urls
from products import views as products_views
from products.views import wishlist_list
from orders import urls as orders_urls
from users import views as users_views
from django.contrib.auth import views as auth_views

from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    path("__reload__/", include("django_browser_reload.urls")),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
    path("set-language/", views.set_language_custom, name="set_language_custom"),
]

urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    # path("about/", views.about, name="about"),
    path("search/", products_views.product_list, name="search"),
    path(
        "products/",
        include((products_urls.urlpatterns, "products"), namespace="products"),
    ),
    path(
        "categories/",
        include((products_urls.categories_urls, "categories"), namespace="categories"),
    ),
    path("wishlist/", wishlist_list, name="wishlist"),
    path("cart/", include("cart.urls", namespace="cart")),
    path("orders/", include((orders_urls.urlpatterns, "orders"), namespace="orders")),
    path("register/", users_views.register, name="register"),
    path("login/", users_views.login_view, name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="/"), name="logout"),
    path("profile/", users_views.profile, name="profile"),
    path("users/", include("users.urls", namespace="users")),
    prefix_default_language=True,
)

# Add debug toolbar URLs only in development
if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
