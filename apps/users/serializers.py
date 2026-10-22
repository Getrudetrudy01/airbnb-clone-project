from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    # Admin accounts are created via createsuperuser, never through the public API.
    role = serializers.ChoiceField(
        choices=[User.Role.GUEST, User.Role.HOST],
        default=User.Role.GUEST,
    )

    class Meta:
        model = User
        fields = ["id", "email", "password", "first_name", "last_name", "role"]
        read_only_fields = ["id"]

    def validate_email(self, email):
        email = User.objects.normalize_email(email)
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return email

    def validate(self, attrs):
        # Run Django's password validators against a temporary user so similarity checks work.
        password_user = User(**{k: v for k, v in attrs.items() if k != "password"})
        validate_password(attrs["password"], user=password_user)
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class PublicUserSerializer(serializers.ModelSerializer):
    """What other people may see about a user."""

    name = serializers.CharField(source="display_name", read_only=True)

    class Meta:
        model = User
        fields = ["id", "name"]
        read_only_fields = fields


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "role", "is_demo", "date_joined"]
        read_only_fields = ["id", "email", "role", "is_demo", "date_joined"]
