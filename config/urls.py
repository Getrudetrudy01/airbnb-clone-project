from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from .views import HealthView, spa

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", HealthView.as_view(), name="health"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/", include("apps.users.urls")),
    path("api/", include("apps.properties.urls")),
    path("api/", include("apps.bookings.urls")),
    path("api/", include("apps.reviews.urls")),
    path("api/", include("apps.payments.urls")),
]

if settings.DEBUG or settings.SERVE_MEDIA:
    # Uploaded photos from local disk. With a storage bucket configured, photo URLs point there instead.
    urlpatterns.append(re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}))

# Everything else is a page of the React app. Must stay last.
urlpatterns.append(re_path(r"^(?!api/|admin/|static/|media/).*$", spa, name="spa"))
