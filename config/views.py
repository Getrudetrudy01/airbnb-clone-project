import logging

from django.conf import settings
from django.db import DatabaseError, connection
from django.http import HttpResponse, HttpResponseNotFound
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


def spa(request):
    """Serve the React app's index.html for any page route (/trips, /stays/3, ...).

    React Router takes over in the browser. Assets under /assets/ are served by WhiteNoise.
    """
    index = settings.FRONTEND_DIST / "index.html"
    if not index.is_file():
        return HttpResponseNotFound(
            "The frontend hasn't been built. Run `npm run build` in frontend/, "
            "or use the Vite dev server at http://localhost:3000.",
            content_type="text/plain",
        )
    response = HttpResponse(index.read_bytes(), content_type="text/html; charset=utf-8")
    # Always revalidate, so a new deploy's asset links are picked up immediately.
    response["Cache-Control"] = "no-cache"
    return response
