from django.urls import path
from orders import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("create_order/", views.create_order, name="create_order"),
    path("confirmation/<int:order_id>/", views.order_confirmation, name="confirmation"),
    path("orders/", views.order_list, name="order_list"),
    path("orders/<int:order_id>/", views.order_detail, name="order_detail"),
]
