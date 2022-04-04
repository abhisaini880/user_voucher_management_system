from django.urls import path
from .views import RewardViewSet

reward_list = RewardViewSet.as_view({"get": "list", "post": "create"})
reward_detail = RewardViewSet.as_view({"put": "update"})
# user_bulk = UserViewSet.as_view({"post": "bulk_create", "put": "bulk_update"})

urlpatterns = [
    path("rewards", reward_list, name="reward-list"),
    path("rewards/<int:pk>", reward_detail, name="reward-detail"),
]
