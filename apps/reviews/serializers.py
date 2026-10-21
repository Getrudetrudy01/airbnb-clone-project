from django.utils import timezone
from rest_framework import serializers

from apps.bookings.models import Booking
from apps.users.serializers import PublicUserSerializer

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    author = PublicUserSerializer(read_only=True)
    # Narrowed to the requesting user's bookings in get_fields.
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.none())

    class Meta:
        model = Review
        fields = ["id", "booking", "property", "author", "rating", "comment", "created_at", "updated_at"]
        read_only_fields = ["id", "property", "author", "created_at", "updated_at"]

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")
        if self.instance is not None:
            # The booking can't be swapped once a review exists.
            fields["booking"].read_only = True
        elif request and request.user.is_authenticated:
            # Only offer (and accept) the user's own bookings.
            fields["booking"].queryset = Booking.objects.filter(guest=request.user)
        return fields

    def validate_booking(self, booking):
        if booking.status != Booking.Status.CONFIRMED:
            raise serializers.ValidationError("Only confirmed bookings can be reviewed.")
        if booking.check_out > timezone.localdate():
            raise serializers.ValidationError("You can review a stay once it has ended.")
        if Review.objects.filter(booking=booking).exists():
            raise serializers.ValidationError("You have already reviewed this stay.")
        return booking

    def create(self, validated_data):
        booking = validated_data["booking"]
        return Review.objects.create(author=booking.guest, property=booking.property, **validated_data)
