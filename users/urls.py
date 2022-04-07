from django.urls import path, include
from .api import LoginAPI, UserViewSet, PingAPI
from knox import views as knox_views

user_list = UserViewSet.as_view({"get": "list", "post": "create"})
user_detail = UserViewSet.as_view({"get": "retrieve", "put": "update"})
user_bulk = UserViewSet.as_view({"post": "bulk_create", "put": "bulk_update"})

urlpatterns = [
    path("auth", include("knox.urls")),
    path("auth/login", LoginAPI.as_view()),
    path("ping", PingAPI.as_view()),
    path("auth/logout", knox_views.LogoutView.as_view(), name="knox_logout"),
    path("users", user_list, name="user-list"),
    path("users/<int:pk>", user_detail, name="user-detail"),
    path("users/bulk", user_bulk, name="user-bulk"),
]
