from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, viewsets

from .models import Review
from .permissions import IsAuthorOrReadOnly
from .serializers import ReviewSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    """Public list of reviews; guests review their own completed stays."""

    queryset = Review.objects.select_related("author")
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["property", "rating"]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
