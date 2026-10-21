from rest_framework.routers import SimpleRouter

from .views import ReviewViewSet

app_name = "reviews"

router = SimpleRouter()
router.register("reviews", ReviewViewSet, basename="review")

urlpatterns = router.urls
