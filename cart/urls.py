from django.urls import path, include
from .views import OrderViewSet
from knox import views as knox_views

order_list = OrderViewSet.as_view({"get": "list", "post": "create"})
order_detail = OrderViewSet.as_view({"get": "retrieve", "put": "update"})

urlpatterns = [
    path("orders", order_list, name="order-list"),
    path("orders/<str:pk>", order_detail, name="order-detail"),
]
