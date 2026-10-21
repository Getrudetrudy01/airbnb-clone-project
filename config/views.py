import logging

from django.db import DatabaseError, connection
from drf_spectacular.utils import extend_schema
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class HealthView(APIView):
    """Liveness/readiness probe for the hosting platform. Checks the database connection."""

    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    throttle_classes = []

    @extend_schema(exclude=True)
    def get(self, request):
        try:
            connection.ensure_connection()
        except DatabaseError:
            logger.exception("Health check: database unavailable")
            return Response({"status": "error", "database": "unavailable"}, status=503)
        return Response({"status": "ok"})
