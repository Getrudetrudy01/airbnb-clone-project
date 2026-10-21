from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ["id", "property", "guest", "check_in", "check_out", "guests", "total_price", "status"]
    list_filter = ["status", "check_in"]
    search_fields = ["property__title", "guest__email"]
    raw_id_fields = ["property", "guest"]
    date_hierarchy = "check_in"
