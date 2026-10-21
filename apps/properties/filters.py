import django_filters
from rest_framework.exceptions import ValidationError

from apps.bookings.models import Booking

from .models import Property


class PropertyFilter(django_filters.FilterSet):
    city = django_filters.CharFilter(lookup_expr="icontains")
    country = django_filters.CharFilter(lookup_expr="icontains")
    min_price = django_filters.NumberFilter(field_name="price_per_night", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price_per_night", lookup_expr="lte")
    guests = django_filters.NumberFilter(field_name="max_guests", lookup_expr="gte")
    check_in = django_filters.DateFilter(method="filter_available")
    check_out = django_filters.DateFilter(method="filter_available")

    class Meta:
        model = Property
        fields = ["city", "country", "min_price", "max_price", "guests"]

    def filter_available(self, queryset, name, value):
        # Both dates are handled together in filter_queryset; this is a no-op per field.
        return queryset

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        check_in = self.form.cleaned_data.get("check_in")
        check_out = self.form.cleaned_data.get("check_out")
        if not (check_in or check_out):
            return queryset
        if not (check_in and check_out):
            raise ValidationError("Provide both check_in and check_out to filter by availability.")
        if check_out <= check_in:
            raise ValidationError("check_out must be after check_in.")
        booked = Booking.objects.overlapping(check_in, check_out).values("property_id")
        return queryset.exclude(id__in=booked)
