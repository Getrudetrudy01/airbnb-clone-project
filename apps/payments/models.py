from django.db import models


class Payment(models.Model):
    """A booking's payment. Card details never touch our server; Stripe holds them."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    booking = models.OneToOneField("bookings.Booking", on_delete=models.CASCADE, related_name="payment")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3)
    payment_method = models.CharField(max_length=30, default="card")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True)
    stripe_checkout_session_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.amount} {self.currency.upper()} for booking #{self.booking_id} ({self.status})"
