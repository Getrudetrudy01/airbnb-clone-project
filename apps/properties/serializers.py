from rest_framework import serializers

from apps.users.serializers import PublicUserSerializer

from .models import Property, PropertyImage

MAX_IMAGE_SIZE = 5 * 1024 * 1024


class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ["id", "image", "caption", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_image(self, image):
        if image.size > MAX_IMAGE_SIZE:
            raise serializers.ValidationError(f"Images must be {MAX_IMAGE_SIZE // (1024 * 1024)} MB or smaller.")
        return image


class PropertySerializer(serializers.ModelSerializer):
    host = PublicUserSerializer(read_only=True)
    images = PropertyImageSerializer(many=True, read_only=True)
    # Filled in by the view's queryset annotation; absent right after create/update.
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            "id",
            "host",
            "title",
            "description",
            "address",
            "city",
            "country",
            "price_per_night",
            "max_guests",
            "images",
            "average_rating",
            "review_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "host", "images", "created_at", "updated_at"]

    def get_average_rating(self, obj) -> float | None:
        value = getattr(obj, "average_rating", None)
        return round(value, 2) if value is not None else None

    def get_review_count(self, obj) -> int:
        return getattr(obj, "review_count", 0)
