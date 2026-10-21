from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import CheckoutView, PaymentViewSet, StripeWebhookView

app_name = "payments"

router = SimpleRouter()
router.register("payments", PaymentViewSet, basename="payment")

urlpatterns = [
    path("payments/checkout/", CheckoutView.as_view(), name="checkout"),
    path("payments/webhook/", StripeWebhookView.as_view(), name="stripe-webhook"),
    *router.urls,
]
