from django.urls import path

from products.views import (
    product_list,
    product_detail,
    category_list,
    category_detail,
    wishlist_list,
    toggle_wishlist,
    add_review,
)

app_name = "products"

urlpatterns = [
    path("", product_list, name="products"),
    path("wishlist/", wishlist_list, name="wishlist_list"),
    path("wishlist/toggle/<int:product_id>/", toggle_wishlist, name="toggle_wishlist"),
    path("review/add/<int:product_id>/", add_review, name="add_review"),
    path("<slug:slug>/", product_detail, name="detail"),
]

categories_urls = [
    path("", category_list, name="categories"),
    path("<slug:slug>/", category_detail, name="detail"),
]
