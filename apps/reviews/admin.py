from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["property", "author", "rating", "created_at"]
    list_filter = ["rating"]
    search_fields = ["property__title", "author__email", "comment"]
    raw_id_fields = ["booking", "property", "author"]
