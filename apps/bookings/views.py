from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import Booking
from .serializers import BookingSerializer


class BookingViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Bookings the current user made as a guest, or received as a host.

    Bookings are never edited or deleted: to change dates, cancel and book again.
    """

    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status", "property"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):  # API schema generation has no real user.
            return Booking.objects.none()
        user = self.request.user
        return Booking.objects.select_related("property", "guest").filter(Q(guest=user) | Q(property__host=user))

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        booking = services.confirm_booking(booking_id=self.get_object().pk, user=request.user)
        return Response(self.get_serializer(booking).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        booking = services.cancel_booking(booking_id=self.get_object().pk, user=request.user)
        return Response(self.get_serializer(booking).data)
