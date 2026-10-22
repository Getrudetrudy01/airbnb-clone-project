from datetime import timedelta
from types import SimpleNamespace
from unittest import mock

import pytest
import stripe
from django.utils import timezone

from apps.bookings.models import Booking

from .models import Payment

CHECKOUT_URL = "/api/payments/checkout/"
WEBHOOK_URL = "/api/payments/webhook/"


@pytest.fixture(autouse=True)
def stripe_settings(settings):
    settings.STRIPE_SECRET_KEY = "sk_test_dummy"
    settings.STRIPE_WEBHOOK_SECRET = "whsec_dummy"
    settings.PAYMENTS_CURRENCY = "usd"
    settings.FRONTEND_URL = "http://frontend.test"


@pytest.fixture
def booking(guest, make_property):
    listing = make_property(price_per_night="99.99")
    start = timezone.localdate() + timedelta(days=10)
    return Booking.objects.create(
        guest=guest, property=listing, check_in=start, check_out=start + timedelta(days=2), total_price="199.98"
    )


@pytest.fixture
def stripe_create():
    session = SimpleNamespace(id="cs_test_123", url="https://checkout.stripe.test/cs_test_123")
    with mock.patch("stripe.checkout.Session.create", return_value=session) as create:
        yield create


@pytest.fixture
def stripe_refund():
    with mock.patch("stripe.Refund.create") as refund:
        yield refund


def send_webhook(client, event_type, session):
    event = stripe.Event.construct_from(
        {"id": "evt_test", "type": event_type, "data": {"object": session}}, "sk_test_dummy"
    )
    with mock.patch("stripe.Webhook.construct_event", return_value=event):
        return client.post(WEBHOOK_URL, data=b"{}", content_type="application/json", HTTP_STRIPE_SIGNATURE="t=1,v1=x")


def paid_session(booking, session_id="cs_test_123"):
    return {
        "id": session_id,
        "payment_status": "paid",
        "payment_intent": "pi_test_123",
        "metadata": {"booking_id": str(booking.pk)},
    }


# --- Starting checkout ----------------------------------------------------


@pytest.mark.django_db
def test_guest_starts_checkout(api_client, guest, booking, stripe_create):
    api_client.force_authenticate(guest)
    response = api_client.post(CHECKOUT_URL, {"booking": booking.pk}, format="json")

    assert response.status_code == 201
    assert response.data["checkout_url"] == "https://checkout.stripe.test/cs_test_123"

    params = stripe_create.call_args.kwargs
    assert params["line_items"][0]["price_data"]["unit_amount"] == 19998
    assert params["metadata"] == {"booking_id": str(booking.pk)}
    assert params["success_url"].startswith("http://frontend.test/")

    payment = Payment.objects.get()
    assert payment.status == Payment.Status.PENDING
    assert payment.stripe_checkout_session_id == "cs_test_123"


@pytest.mark.django_db
def test_only_the_guest_can_pay(api_client, booking, make_user, stripe_create):
    for user in (make_user(), booking.property.host):
        api_client.force_authenticate(user)
        assert api_client.post(CHECKOUT_URL, {"booking": booking.pk}, format="json").status_code == 404
    stripe_create.assert_not_called()


@pytest.mark.django_db
def test_cannot_pay_cancelled_booking(api_client, guest, booking, stripe_create):
    booking.status = Booking.Status.CANCELLED
    booking.save()
    api_client.force_authenticate(guest)
    assert api_client.post(CHECKOUT_URL, {"booking": booking.pk}, format="json").status_code == 400


@pytest.mark.django_db
def test_cannot_pay_twice(api_client, guest, booking, stripe_create):
    Payment.objects.create(booking=booking, amount="199.98", currency="usd", status=Payment.Status.COMPLETED)
    api_client.force_authenticate(guest)
    assert api_client.post(CHECKOUT_URL, {"booking": booking.pk}, format="json").status_code == 400


@pytest.mark.django_db
def test_retrying_checkout_expires_previous_session(api_client, guest, booking, stripe_create):
    Payment.objects.create(booking=booking, amount="199.98", currency="usd", stripe_checkout_session_id="cs_test_old")
    api_client.force_authenticate(guest)
    with mock.patch("stripe.checkout.Session.expire") as expire:
        assert api_client.post(CHECKOUT_URL, {"booking": booking.pk}, format="json").status_code == 201
    expire.assert_called_once_with("cs_test_old", api_key="sk_test_dummy")
    assert Payment.objects.get().stripe_checkout_session_id == "cs_test_123"


@pytest.mark.django_db
def test_checkout_unavailable_without_stripe_key(api_client, guest, booking, settings):
    settings.STRIPE_SECRET_KEY = ""
    api_client.force_authenticate(guest)
    assert api_client.post(CHECKOUT_URL, {"booking": booking.pk}, format="json").status_code == 503


@pytest.mark.django_db
def test_stripe_error_returns_502(api_client, guest, booking):
    api_client.force_authenticate(guest)
    with mock.patch("stripe.checkout.Session.create", side_effect=stripe.APIConnectionError("down")):
        assert api_client.post(CHECKOUT_URL, {"booking": booking.pk}, format="json").status_code == 502
    assert not Payment.objects.exists()


# --- Webhooks -------------------------------------------------------------


@pytest.fixture
def pending_payment(booking):
    return Payment.objects.create(
        booking=booking, amount="199.98", currency="usd", stripe_checkout_session_id="cs_test_123"
    )


@pytest.mark.django_db
def test_webhook_rejects_bad_signature(api_client, pending_payment):
    response = api_client.post(
        WEBHOOK_URL, data=b"{}", content_type="application/json", HTTP_STRIPE_SIGNATURE="t=1,v1=bogus"
    )
    assert response.status_code == 400
    pending_payment.refresh_from_db()
    assert pending_payment.status == Payment.Status.PENDING


@pytest.mark.django_db
def test_successful_payment_confirms_booking(api_client, booking, pending_payment):
    response = send_webhook(api_client, "checkout.session.completed", paid_session(booking))
    assert response.status_code == 200

    pending_payment.refresh_from_db()
    booking.refresh_from_db()
    assert pending_payment.status == Payment.Status.COMPLETED
    assert pending_payment.stripe_payment_intent_id == "pi_test_123"
    assert booking.status == Booking.Status.CONFIRMED


@pytest.mark.django_db
def test_duplicate_webhook_is_harmless(api_client, booking, pending_payment):
    send_webhook(api_client, "checkout.session.completed", paid_session(booking))
    assert send_webhook(api_client, "checkout.session.completed", paid_session(booking)).status_code == 200
    pending_payment.refresh_from_db()
    assert pending_payment.status == Payment.Status.COMPLETED


@pytest.mark.django_db
def test_unpaid_completion_does_not_confirm(api_client, booking, pending_payment):
    # Delayed payment methods complete the session before the money arrives.
    session = {**paid_session(booking), "payment_status": "unpaid"}
    send_webhook(api_client, "checkout.session.completed", session)
    booking.refresh_from_db()
    assert booking.status == Booking.Status.PENDING


@pytest.mark.django_db
def test_expired_session_marks_payment_failed(api_client, booking, pending_payment):
    send_webhook(api_client, "checkout.session.expired", paid_session(booking))
    pending_payment.refresh_from_db()
    booking.refresh_from_db()
    assert pending_payment.status == Payment.Status.FAILED
    assert booking.status == Booking.Status.PENDING  # The guest can try paying again.


@pytest.mark.django_db
def test_expiry_of_replaced_session_is_ignored(api_client, booking, pending_payment):
    send_webhook(api_client, "checkout.session.expired", paid_session(booking, session_id="cs_test_old"))
    pending_payment.refresh_from_db()
    assert pending_payment.status == Payment.Status.PENDING


@pytest.mark.django_db
def test_payment_after_cancellation_is_refunded(api_client, booking, pending_payment, stripe_refund):
    booking.status = Booking.Status.CANCELLED
    booking.save()

    send_webhook(api_client, "checkout.session.completed", paid_session(booking))

    stripe_refund.assert_called_once_with(api_key="sk_test_dummy", payment_intent="pi_test_123")
    pending_payment.refresh_from_db()
    booking.refresh_from_db()
    assert pending_payment.status == Payment.Status.REFUNDED
    assert booking.status == Booking.Status.CANCELLED


# --- Refunds on cancellation -----------------------------------------------


@pytest.mark.django_db
def test_cancelling_paid_booking_refunds(api_client, guest, booking, stripe_refund):
    Payment.objects.create(
        booking=booking,
        amount="199.98",
        currency="usd",
        status=Payment.Status.COMPLETED,
        stripe_payment_intent_id="pi_test_123",
    )
    api_client.force_authenticate(guest)
    assert api_client.post(f"/api/bookings/{booking.pk}/cancel/").status_code == 200
    stripe_refund.assert_called_once_with(api_key="sk_test_dummy", payment_intent="pi_test_123")
    assert Payment.objects.get().status == Payment.Status.REFUNDED


@pytest.mark.django_db
def test_failed_refund_keeps_booking_active(api_client, guest, booking):
    Payment.objects.create(
        booking=booking,
        amount="199.98",
        currency="usd",
        status=Payment.Status.COMPLETED,
        stripe_payment_intent_id="pi_test_123",
    )
    api_client.force_authenticate(guest)
    with mock.patch("stripe.Refund.create", side_effect=stripe.APIConnectionError("down")):
        assert api_client.post(f"/api/bookings/{booking.pk}/cancel/").status_code == 502
    booking.refresh_from_db()
    assert booking.status == Booking.Status.PENDING
    assert Payment.objects.get().status == Payment.Status.COMPLETED


# --- Listing payments -----------------------------------------------------


@pytest.mark.django_db
def test_payments_visible_to_guest_and_host_only(api_client, booking, pending_payment, make_user):
    for user, expected in [(booking.guest, 1), (booking.property.host, 1), (make_user(), 0)]:
        api_client.force_authenticate(user)
        assert api_client.get("/api/payments/").data["count"] == expected


# --- Late payments for expired reservations ----------------------------------


def age(booking, minutes):
    from datetime import timedelta as td

    Booking.objects.filter(pk=booking.pk).update(created_at=timezone.now() - td(minutes=minutes))
    booking.refresh_from_db()


@pytest.mark.django_db
def test_cannot_start_checkout_for_expired_reservation(api_client, guest, booking, stripe_create, settings):
    settings.BOOKING_PAYMENT_WINDOW_MINUTES = 60
    age(booking, 90)
    api_client.force_authenticate(guest)
    assert api_client.post(CHECKOUT_URL, {"booking": booking.pk}, format="json").status_code == 400
    stripe_create.assert_not_called()


@pytest.mark.django_db
def test_late_payment_is_confirmed_when_dates_still_free(api_client, booking, pending_payment, settings):
    settings.BOOKING_PAYMENT_WINDOW_MINUTES = 60
    age(booking, 90)
    send_webhook(api_client, "checkout.session.completed", paid_session(booking))
    booking.refresh_from_db()
    assert booking.status == Booking.Status.CONFIRMED


@pytest.mark.django_db
def test_late_payment_is_refunded_when_dates_were_rebooked(
    api_client, booking, pending_payment, stripe_refund, make_user, settings
):
    settings.BOOKING_PAYMENT_WINDOW_MINUTES = 60
    age(booking, 90)
    # Someone else booked the released dates.
    Booking.objects.create(
        guest=make_user(),
        property=booking.property,
        check_in=booking.check_in,
        check_out=booking.check_out,
        total_price="199.98",
        status=Booking.Status.CONFIRMED,
    )

    send_webhook(api_client, "checkout.session.completed", paid_session(booking))

    stripe_refund.assert_called_once_with(api_key="sk_test_dummy", payment_intent="pi_test_123")
    booking.refresh_from_db()
    pending_payment.refresh_from_db()
    assert booking.status == Booking.Status.CANCELLED
    assert pending_payment.status == Payment.Status.REFUNDED
