from rest_framework import routers
from wholesellers.api import WholeSellerViewSet

router = routers.DefaultRouter(trailing_slash=False)
router.register("", WholeSellerViewSet, basename="dashboard")

urlpatterns = router.urls
