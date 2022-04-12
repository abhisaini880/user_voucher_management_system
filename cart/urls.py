from django.urls import path

from .views import OrderViewSet, TransactionViewSet, PointViewSet

order_list = OrderViewSet.as_view({"get": "list", "post": "create"})
order_detail = OrderViewSet.as_view({"get": "retrieve", "put": "update"})
transaction_list = TransactionViewSet.as_view({"get": "list"})
transaction_details = TransactionViewSet.as_view({"get": "retrieve"})
point_list = PointViewSet.as_view({"get": "list"})
point_details = PointViewSet.as_view({"get": "retrieve"})
order_bulk = OrderViewSet.as_view({"put": "bulk_update"})

urlpatterns = [
    path("orders", order_list, name="order-list"),
    path("orders/<str:pk>", order_detail, name="order-detail"),
    path("transactions", transaction_list, name="transaction-list"),
    path(
        "orders/<str:pk>/transactions",
        transaction_details,
        name="transaction-details",
    ),
    path("points/summary", point_list, name="point-list"),
    path(
        "users/<int:pk>/points/summary",
        point_details,
        name="point-details",
    ),
    path("order/bulk", order_bulk, name="order-update"),
]
