import logging
import time
from decimal import Decimal

import stripe
from django.conf import settings
from django.db import transaction
from rest_framework.exceptions import APIException, NotFound, ValidationError

from apps.bookings.models import Booking
from apps.properties.models import Property

from .models import Payment

logger = logging.getLogger(__name__)

# Stripe requires Checkout Sessions to stay open for at least 30 minutes.
CHECKOUT_SESSION_LIFETIME_SECONDS = 31 * 60


class PaymentsNotConfigured(APIException):
    status_code = 503
    default_detail = "Payments are not configured on this server."


class PaymentProviderError(APIException):
    status_code = 502
    default_detail = "The payment provider could not process the request. Please try again."


def _api_key():
    if not settings.STRIPE_SECRET_KEY:
        raise PaymentsNotConfigured()
    return settings.STRIPE_SECRET_KEY


def _to_minor_units(amount):
    """Stripe expects amounts in the smallest currency unit (e.g. cents)."""
    return int((Decimal(amount) * 100).quantize(Decimal("1")))


@transaction.atomic
def start_checkout(*, booking_id, user):
    """Create a Stripe Checkout Session for the guest's booking and return its URL."""
    api_key = _api_key()
    try:
        booking = Booking.objects.select_for_update().select_related("property").get(pk=booking_id, guest=user)
    except Booking.DoesNotExist as exc:
        raise NotFound("Booking not found.") from exc

    if booking.status == Booking.Status.CANCELLED:
        raise ValidationError({"booking": "This booking has been cancelled."})
    if booking.is_expired:
        raise ValidationError({"booking": "This reservation expired because it wasn't paid in time."})

    payment = Payment.objects.filter(booking=booking).first()
    if payment and payment.status in (Payment.Status.COMPLETED, Payment.Status.REFUNDED):
        raise ValidationError({"booking": "This booking has already been paid."})

    try:
        if payment and payment.status == Payment.Status.PENDING and payment.stripe_checkout_session_id:
            # Close the previous checkout page so the guest can't pay twice.
            _expire_session_quietly(payment.stripe_checkout_session_id, api_key)

        session = stripe.checkout.Session.create(
            api_key=api_key,
            mode="payment",
            line_items=[
                {
                    "quantity": 1,
                    "price_data": {
                        "currency": settings.PAYMENTS_CURRENCY,
                        "unit_amount": _to_minor_units(booking.total_price),
                        "product_data": {
                            "name": booking.property.title,
                            "description": f"{booking.nights} nights, {booking.check_in} to {booking.check_out}",
                        },
                    },
                }
            ],
            client_reference_id=str(booking.pk),
            metadata={"booking_id": str(booking.pk)},
            customer_email=user.email,
            success_url=f"{settings.FRONTEND_URL}/bookings/{booking.pk}?payment=success",
            cancel_url=f"{settings.FRONTEND_URL}/bookings/{booking.pk}?payment=cancelled",
            expires_at=int(time.time()) + CHECKOUT_SESSION_LIFETIME_SECONDS,
        )
    except stripe.StripeError as exc:
        logger.exception("Stripe checkout creation failed for booking %s", booking.pk)
        raise PaymentProviderError() from exc

    Payment.objects.update_or_create(
        booking=booking,
        defaults={
            "amount": booking.total_price,
            "currency": settings.PAYMENTS_CURRENCY,
            "status": Payment.Status.PENDING,
            "stripe_checkout_session_id": session.id,
            "stripe_payment_intent_id": "",
        },
    )
    return session.url


def _expire_session_quietly(session_id, api_key):
    try:
        stripe.checkout.Session.expire(session_id, api_key=api_key)
    except stripe.StripeError:
        # Already expired or completed; a completed one will still arrive via webhook.
        logger.info("Could not expire checkout session %s", session_id)


def refund(payment):
    """Refund a completed payment in full. Call inside the caller's transaction."""
    try:
        stripe.Refund.create(api_key=_api_key(), payment_intent=payment.stripe_payment_intent_id)
    except stripe.StripeError as exc:
        logger.exception("Stripe refund failed for payment %s", payment.pk)
        raise PaymentProviderError() from exc
    payment.status = Payment.Status.REFUNDED
    payment.save(update_fields=["status", "updated_at"])


# --- Webhooks --------------------------------------------------------------


def handle_event(event):
    """Apply a verified Stripe webhook event. Safe to call more than once per event."""
    session = event["data"]["object"]
    event_type = event["type"]

    if event_type == "checkout.session.completed" and session.get("payment_status") == "paid":
        _mark_paid(session)
    elif event_type == "checkout.session.async_payment_succeeded":
        _mark_paid(session)
    elif event_type in ("checkout.session.expired", "checkout.session.async_payment_failed"):
        _mark_failed(session)


def _payment_for_session(session):
    booking_id = (session.get("metadata") or {}).get("booking_id")
    if not booking_id:
        return None
    return Payment.objects.select_for_update().select_related("booking").filter(booking_id=booking_id).first()


@transaction.atomic
def _mark_paid(session):
    payment = _payment_for_session(session)
    if payment is None:
        logger.warning("Paid checkout session %s has no matching payment", session.get("id"))
        return
    if payment.status in (Payment.Status.COMPLETED, Payment.Status.REFUNDED):
        return  # Duplicate delivery.

    payment.status = Payment.Status.COMPLETED
    payment.stripe_checkout_session_id = session["id"]
    payment.stripe_payment_intent_id = session.get("payment_intent") or ""
    payment.save()

    booking = Booking.objects.select_for_update().select_related("property").get(pk=payment.booking_id)
    if booking.status == Booking.Status.CANCELLED:
        # The guest cancelled while the checkout page was open: give the money back.
        refund(payment)
    elif booking.status == Booking.Status.PENDING:
        if booking.is_expired and _dates_taken_by_others(booking):
            # A late webhook (e.g. Stripe retrying after an outage) for a reservation whose
            # dates were released and rebooked: refund rather than double-book.
            refund(payment)
            booking.status = Booking.Status.CANCELLED
        else:
            booking.status = Booking.Status.CONFIRMED
        booking.save(update_fields=["status", "updated_at"])


def _dates_taken_by_others(booking):
    # Lock the listing so no new booking can land while we decide.
    Property.objects.select_for_update().get(pk=booking.property_id)
    return (
        Booking.objects.overlapping(booking.check_in, booking.check_out)
        .filter(property_id=booking.property_id)
        .exclude(pk=booking.pk)
        .exists()
    )


@transaction.atomic
def _mark_failed(session):
    payment = _payment_for_session(session)
    # Ignore events for an older session that was replaced by a newer checkout attempt.
    if payment and payment.status == Payment.Status.PENDING and payment.stripe_checkout_session_id == session["id"]:
        payment.status = Payment.Status.FAILED
        payment.save(update_fields=["status", "updated_at"])
