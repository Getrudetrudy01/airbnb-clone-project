from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.users.urls")),
    path("api/", include("apps.properties.urls")),
    path("api/", include("apps.bookings.urls")),
    path("api/", include("apps.reviews.urls")),
    path("api/", include("apps.payments.urls")),
]

if settings.DEBUG:
    # In production, uploaded media is served by the web server or cloud storage.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
