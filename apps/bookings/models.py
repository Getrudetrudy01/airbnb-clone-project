import builtins
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone


def payment_cutoff(now=None):
    """Pending bookings created before this moment have run out of time to pay."""
    return (now or timezone.now()) - timedelta(minutes=settings.BOOKING_PAYMENT_WINDOW_MINUTES)


class BookingQuerySet(models.QuerySet):
    def active(self):
        """Bookings that hold their dates.

        Cancelled bookings free their dates, and so do pending ones left unpaid past the
        payment window. That's enforced here rather than by a scheduled job, so dates are
        released on time even on hosts without cron.
        """
        return self.filter(
            Q(status=Booking.Status.CONFIRMED) | Q(status=Booking.Status.PENDING, created_at__gte=payment_cutoff())
        )

    def overlapping(self, check_in, check_out):
        """Active bookings whose stay overlaps [check_in, check_out).

        Check-out day is exclusive, so a stay ending on the 5th does not clash
        with one starting on the 5th.
        """
        return self.active().filter(check_in__lt=check_out, check_out__gt=check_in)


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    guest = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings")
    property = models.ForeignKey("properties.Property", on_delete=models.CASCADE, related_name="bookings")
    check_in = models.DateField()
    check_out = models.DateField()
    guests = models.PositiveSmallIntegerField(default=1)
    # Stored rather than computed so later price changes don't alter past bookings.
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = BookingQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["property", "check_in", "check_out"])]
        constraints = [
            models.CheckConstraint(condition=Q(check_out__gt=F("check_in")), name="booking_checkout_after_checkin"),
            models.CheckConstraint(condition=Q(guests__gte=1), name="booking_guests_min_1"),
        ]

    def __str__(self):
        return f"{self.guest} @ {self.property} ({self.check_in} → {self.check_out})"

    # The "property" field above shadows the builtin decorator inside this class.
    @builtins.property
    def nights(self):
        return (self.check_out - self.check_in).days

    @builtins.property
    def is_expired(self):
        """Pending and not paid within the payment window: its dates are no longer held."""
        return self.status == self.Status.PENDING and self.created_at < payment_cutoff()

    @builtins.property
    def effective_status(self):
        """The status people should see, whether or not the cleanup job has run yet."""
        return self.Status.CANCELLED if self.is_expired else self.status
