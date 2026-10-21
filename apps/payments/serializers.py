from rest_framework import serializers

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "booking", "amount", "currency", "payment_method", "status", "created_at", "updated_at"]
        read_only_fields = fields


class CheckoutSerializer(serializers.Serializer):
    booking = serializers.IntegerField()
