import logging

import stripe
from django.conf import settings
from django.db.models import Q
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .models import Payment
from .serializers import CheckoutSerializer, PaymentSerializer

logger = logging.getLogger(__name__)


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """Payments for bookings the user made as a guest or received as a host."""

    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):  # API schema generation has no real user.
            return Payment.objects.none()
        user = self.request.user
        return Payment.objects.filter(Q(booking__guest=user) | Q(booking__property__host=user))


class CheckoutView(APIView):
    """Start paying for a booking. Redirect the guest to the returned checkout_url."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CheckoutSerializer

    @extend_schema(
        request=CheckoutSerializer,
        responses={201: inline_serializer("CheckoutResponse", {"checkout_url": serializers.URLField()})},
    )
    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        url = services.start_checkout(booking_id=serializer.validated_data["booking"], user=request.user)
        return Response({"checkout_url": url}, status=status.HTTP_201_CREATED)


class StripeWebhookView(APIView):
    """Receives events from Stripe. Authenticated by the Stripe-Signature header, not a user."""

    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    throttle_classes = []  # Stripe may send bursts of events; the signature check protects this endpoint.

    @extend_schema(exclude=True)
    def post(self, request):
        if not settings.STRIPE_WEBHOOK_SECRET:
            raise services.PaymentsNotConfigured()
        try:
            event = stripe.Webhook.construct_event(
                request.body,
                request.META.get("HTTP_STRIPE_SIGNATURE"),
                settings.STRIPE_WEBHOOK_SECRET,
            )
        except (ValueError, stripe.SignatureVerificationError):
            logger.warning("Rejected Stripe webhook with invalid payload or signature")
            return Response({"detail": "Invalid signature."}, status=status.HTTP_400_BAD_REQUEST)

        # StripeObject isn't a dict (no .get); work with plain data from here on.
        services.handle_event(event.to_dict())
        return Response({"received": True})
