from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, parsers, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.bookings.models import Booking

from .filters import PropertyFilter
from .models import Property
from .permissions import IsHostOrReadOnly, IsOwnerOrReadOnly
from .serializers import PropertyImageSerializer, PropertySerializer


class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.select_related("host").prefetch_related("images")
    serializer_class = PropertySerializer
    permission_classes = [IsHostOrReadOnly, IsOwnerOrReadOnly]
    filterset_class = PropertyFilter
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "description", "city", "country"]
    ordering_fields = ["price_per_night", "created_at"]

    def perform_create(self, serializer):
        serializer.save(host=self.request.user)

    @action(
        detail=True,
        methods=["post"],
        parser_classes=[parsers.MultiPartParser, parsers.FormParser],
        serializer_class=PropertyImageSerializer,
    )
    def images(self, request, pk=None):
        """Upload an image to this listing (owner only)."""
        listing = self.get_object()
        serializer = PropertyImageSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        serializer.save(property=listing)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"], url_path=r"images/(?P<image_id>\d+)")
    def delete_image(self, request, pk=None, image_id=None):
        """Remove an image from this listing (owner only)."""
        listing = self.get_object()
        image = get_object_or_404(listing.images, pk=image_id)
        image.image.delete(save=False)
        image.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get"], url_path="booked-dates", permission_classes=[permissions.AllowAny])
    def booked_dates(self, request, pk=None):
        """Date ranges that are already taken, for showing a calendar."""
        listing = self.get_object()
        ranges = (
            Booking.objects.active()
            .filter(property=listing, check_out__gt=timezone.localdate())
            .order_by("check_in")
            .values("check_in", "check_out")
        )
        return Response(list(ranges))
