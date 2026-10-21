from django.contrib import admin

from .models import Property, PropertyImage


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 0


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ["title", "host", "city", "country", "price_per_night", "max_guests", "created_at"]
    list_filter = ["country", "city"]
    search_fields = ["title", "city", "host__email"]
    raw_id_fields = ["host"]
    inlines = [PropertyImageInline]
