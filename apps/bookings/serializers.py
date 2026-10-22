from django.utils import timezone
from rest_framework import serializers

from apps.properties.models import Property

from . import services
from .models import Booking

MAX_NIGHTS = 90


class BookingSerializer(serializers.ModelSerializer):
    property = serializers.PrimaryKeyRelatedField(queryset=Property.objects.all())
    property_title = serializers.CharField(source="property.title", read_only=True)
    guest = serializers.StringRelatedField(read_only=True)
    nights = serializers.IntegerField(read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "property",
            "property_title",
            "guest",
            "check_in",
            "check_out",
            "nights",
            "guests",
            "total_price",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "total_price", "status", "created_at"]

    def validate(self, attrs):
        check_in, check_out = attrs["check_in"], attrs["check_out"]
        if check_in < timezone.localdate():
            raise serializers.ValidationError({"check_in": "Check-in cannot be in the past."})
        if check_out <= check_in:
            raise serializers.ValidationError({"check_out": "Check-out must be after check-in."})
        if (check_out - check_in).days > MAX_NIGHTS:
            raise serializers.ValidationError({"check_out": f"Stays are limited to {MAX_NIGHTS} nights."})
        if attrs.get("guests", 1) < 1:
            raise serializers.ValidationError({"guests": "At least one guest is required."})
        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Unpaid bookings past the payment window show as cancelled even before cleanup runs.
        data["status"] = instance.effective_status
        return data

    def create(self, validated_data):
        return services.create_booking(
            guest=self.context["request"].user,
            property_id=validated_data["property"].pk,
            check_in=validated_data["check_in"],
            check_out=validated_data["check_out"],
            guests=validated_data.get("guests", 1),
        )
