from rest_framework import serializers

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
    host = serializers.StringRelatedField(read_only=True)
    images = PropertyImageSerializer(many=True, read_only=True)

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
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "host", "images", "created_at", "updated_at"]
