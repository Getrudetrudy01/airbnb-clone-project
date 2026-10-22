from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.payments import services as payment_services
from apps.payments.models import Payment
from apps.properties.models import Property

from .models import Booking, payment_cutoff

EXPIRED_MESSAGE = "This reservation expired because it wasn't paid in time. Book the dates again."


def expire_unpaid_bookings(*, now=None):
    """Mark pending bookings left unpaid past the payment window as cancelled.

    Expired bookings already stop holding dates (see BookingQuerySet.active), so this
    only tidies their stored status. Returns how many were cancelled.
    """
    cutoff = payment_cutoff(now)
    stale_ids = list(
        Booking.objects.filter(status=Booking.Status.PENDING, created_at__lt=cutoff)
        .exclude(payment__status=Payment.Status.COMPLETED)
        .values_list("pk", flat=True)
    )

    cancelled = 0
    for booking_id in stale_ids:
        # One transaction per booking, re-checked under lock, so a payment landing
        # mid-run is never cancelled.
        with transaction.atomic():
            booking = Booking.objects.select_for_update().get(pk=booking_id)
            payment = Payment.objects.select_for_update().filter(booking=booking).first()
            if booking.status != Booking.Status.PENDING or (payment and payment.status == Payment.Status.COMPLETED):
                continue
            booking.status = Booking.Status.CANCELLED
            booking.save(update_fields=["status", "updated_at"])
            if payment and payment.status == Payment.Status.PENDING:
                payment.status = Payment.Status.FAILED
                payment.save(update_fields=["status", "updated_at"])
            cancelled += 1
    return cancelled


@transaction.atomic
def create_booking(*, guest, property_id, check_in, check_out, guests):
    """Create a pending booking, guaranteeing no overlap with existing ones.

    The property row is locked (SELECT ... FOR UPDATE) for the duration of the
    transaction, so two simultaneous requests for the same dates are handled
    one after the other and the second one sees the first booking.
    """
    listing = Property.objects.select_for_update().get(pk=property_id)

    if listing.host_id == guest.id:
        raise ValidationError({"property": "You cannot book your own property."})
    if guests > listing.max_guests:
        raise ValidationError({"guests": f"This property allows at most {listing.max_guests} guests."})
    if Booking.objects.overlapping(check_in, check_out).filter(property=listing).exists():
        raise ValidationError({"non_field_errors": ["These dates are not available."]})

    nights = (check_out - check_in).days
    return Booking.objects.create(
        guest=guest,
        property=listing,
        check_in=check_in,
        check_out=check_out,
        guests=guests,
        total_price=listing.price_per_night * nights,
    )


@transaction.atomic
def confirm_booking(*, booking_id, user):
    booking = Booking.objects.select_for_update().select_related("property").get(pk=booking_id)
    if booking.property.host_id != user.id:
        raise PermissionDenied("Only the host can confirm this booking.")
    if booking.is_expired:
        raise ValidationError({"status": EXPIRED_MESSAGE})
    if booking.status != Booking.Status.PENDING:
        raise ValidationError({"status": f"Cannot confirm a {booking.status} booking."})
    booking.status = Booking.Status.CONFIRMED
    booking.save(update_fields=["status", "updated_at"])
    return booking


@transaction.atomic
def cancel_booking(*, booking_id, user):
    booking = Booking.objects.select_for_update().select_related("property").get(pk=booking_id)
    if user.id not in (booking.guest_id, booking.property.host_id):
        raise PermissionDenied("You cannot cancel this booking.")
    if booking.status == Booking.Status.CANCELLED:
        raise ValidationError({"status": "This booking is already cancelled."})
    if booking.check_in <= timezone.localdate():
        raise ValidationError({"status": "Bookings cannot be cancelled on or after the check-in date."})
    booking.status = Booking.Status.CANCELLED
    booking.save(update_fields=["status", "updated_at"])

    payment = Payment.objects.select_for_update().filter(booking=booking).first()
    if payment and payment.status == Payment.Status.COMPLETED:
        # If the refund fails, the whole transaction rolls back and the booking stays active.
        payment_services.refund(payment)
    return booking
