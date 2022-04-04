from django.urls import path
from .views import WindowViewSet

window_list = WindowViewSet.as_view(
    {"get": "list", "post": "create", "put": "update"}
)
window_custom = WindowViewSet.as_view({"get": "active_window"})

urlpatterns = [
    path("reedem/window", window_list, name="window-list"),
    path("reedem/window/active", window_custom, name="window-active"),
]
