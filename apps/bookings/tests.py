from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from .models import Booking

LIST_URL = "/api/bookings/"


def days_from_now(n):
    return timezone.localdate() + timedelta(days=n)


def book(client, listing, check_in, check_out, guests=1):
    payload = {"property": listing.pk, "check_in": check_in, "check_out": check_out, "guests": guests}
    return client.post(LIST_URL, payload, format="json")


@pytest.fixture
def listing(make_property):
    return make_property(price_per_night="100.00", max_guests=4)


@pytest.fixture
def guest_client(api_client, guest):
    api_client.force_authenticate(guest)
    return api_client


# --- Creating bookings ----------------------------------------------------


@pytest.mark.django_db
def test_guest_can_book_and_price_is_calculated(guest_client, guest, listing):
    response = book(guest_client, listing, days_from_now(5), days_from_now(8), guests=2)
    assert response.status_code == 201
    assert response.data["status"] == "pending"
    assert response.data["nights"] == 3
    assert Decimal(response.data["total_price"]) == Decimal("300.00")
    assert Booking.objects.get().guest == guest


@pytest.mark.django_db
def test_anonymous_cannot_book(api_client, listing):
    assert book(api_client, listing, days_from_now(5), days_from_now(8)).status_code == 401


@pytest.mark.django_db
def test_overlapping_booking_is_rejected(guest_client, listing, make_user, api_client):
    assert book(guest_client, listing, days_from_now(5), days_from_now(10)).status_code == 201

    guest_client.force_authenticate(make_user())
    for check_in, check_out in [(3, 6), (9, 12), (6, 8), (4, 11)]:
        response = book(guest_client, listing, days_from_now(check_in), days_from_now(check_out))
        assert response.status_code == 400, (check_in, check_out)
    assert Booking.objects.count() == 1


@pytest.mark.django_db
def test_back_to_back_bookings_are_allowed(guest_client, listing):
    assert book(guest_client, listing, days_from_now(5), days_from_now(10)).status_code == 201
    # Check-in on the day the previous guest checks out.
    assert book(guest_client, listing, days_from_now(10), days_from_now(12)).status_code == 201
    assert book(guest_client, listing, days_from_now(3), days_from_now(5)).status_code == 201


@pytest.mark.django_db
def test_cancelled_booking_frees_dates(guest_client, listing):
    first = book(guest_client, listing, days_from_now(5), days_from_now(10)).data
    guest_client.post(f"{LIST_URL}{first['id']}/cancel/")
    assert book(guest_client, listing, days_from_now(5), days_from_now(10)).status_code == 201


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("check_in", "check_out", "guests", "field"),
    [
        (-1, 2, 1, "check_in"),  # in the past
        (5, 5, 1, "check_out"),  # zero nights
        (5, 3, 1, "check_out"),  # check-out before check-in
        (5, 100, 1, "check_out"),  # too long
        (5, 7, 5, "guests"),  # over max_guests
        (5, 7, 0, "guests"),  # no guests
    ],
)
def test_invalid_bookings_are_rejected(guest_client, listing, check_in, check_out, guests, field):
    response = book(guest_client, listing, days_from_now(check_in), days_from_now(check_out), guests)
    assert response.status_code == 400
    assert field in response.data


@pytest.mark.django_db
def test_host_cannot_book_own_property(api_client, listing):
    api_client.force_authenticate(listing.host)
    response = book(api_client, listing, days_from_now(5), days_from_now(7))
    assert response.status_code == 400
    assert "property" in response.data


@pytest.mark.django_db
def test_client_cannot_set_price_or_status(guest_client, listing):
    payload = {
        "property": listing.pk,
        "check_in": days_from_now(5),
        "check_out": days_from_now(7),
        "total_price": "1.00",
        "status": "confirmed",
    }
    response = guest_client.post(LIST_URL, payload, format="json")
    assert response.status_code == 201
    assert response.data["status"] == "pending"
    assert Decimal(response.data["total_price"]) == Decimal("200.00")


# --- Visibility -----------------------------------------------------------


@pytest.mark.django_db
def test_users_only_see_their_own_bookings(api_client, guest, listing, make_user):
    api_client.force_authenticate(guest)
    booking_id = book(api_client, listing, days_from_now(5), days_from_now(7)).data["id"]

    # The host of the property sees it too.
    api_client.force_authenticate(listing.host)
    assert [b["id"] for b in api_client.get(LIST_URL).data["results"]] == [booking_id]

    # A stranger sees nothing and cannot open it.
    api_client.force_authenticate(make_user())
    assert api_client.get(LIST_URL).data["count"] == 0
    assert api_client.get(f"{LIST_URL}{booking_id}/").status_code == 404


@pytest.mark.django_db
def test_bookings_cannot_be_edited_or_deleted(guest_client, listing):
    booking_id = book(guest_client, listing, days_from_now(5), days_from_now(7)).data["id"]
    url = f"{LIST_URL}{booking_id}/"
    assert guest_client.patch(url, {"guests": 2}, format="json").status_code == 405
    assert guest_client.delete(url).status_code == 405


# --- Confirm / cancel -----------------------------------------------------


@pytest.mark.django_db
def test_host_can_confirm(api_client, guest, listing):
    api_client.force_authenticate(guest)
    booking_id = book(api_client, listing, days_from_now(5), days_from_now(7)).data["id"]

    api_client.force_authenticate(listing.host)
    response = api_client.post(f"{LIST_URL}{booking_id}/confirm/")
    assert response.status_code == 200
    assert response.data["status"] == "confirmed"

    # Confirming twice is an error.
    assert api_client.post(f"{LIST_URL}{booking_id}/confirm/").status_code == 400


@pytest.mark.django_db
def test_guest_cannot_confirm(guest_client, listing):
    booking_id = book(guest_client, listing, days_from_now(5), days_from_now(7)).data["id"]
    assert guest_client.post(f"{LIST_URL}{booking_id}/confirm/").status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize("canceller", ["guest", "host"])
def test_guest_or_host_can_cancel(api_client, guest, listing, canceller):
    api_client.force_authenticate(guest)
    booking_id = book(api_client, listing, days_from_now(5), days_from_now(7)).data["id"]

    api_client.force_authenticate(guest if canceller == "guest" else listing.host)
    response = api_client.post(f"{LIST_URL}{booking_id}/cancel/")
    assert response.status_code == 200
    assert response.data["status"] == "cancelled"
    assert api_client.post(f"{LIST_URL}{booking_id}/cancel/").status_code == 400


@pytest.mark.django_db
def test_cannot_cancel_after_check_in(guest_client, guest, listing):
    booking = Booking.objects.create(
        guest=guest, property=listing, check_in=days_from_now(0), check_out=days_from_now(2), total_price="200.00"
    )
    assert guest_client.post(f"{LIST_URL}{booking.pk}/cancel/").status_code == 400


# --- Booked dates calendar ------------------------------------------------


@pytest.mark.django_db
def test_booked_dates_lists_active_future_ranges(api_client, guest, listing):
    Booking.objects.create(
        guest=guest, property=listing, check_in=days_from_now(5), check_out=days_from_now(7), total_price="200.00"
    )
    Booking.objects.create(
        guest=guest,
        property=listing,
        check_in=days_from_now(10),
        check_out=days_from_now(12),
        total_price="200.00",
        status=Booking.Status.CANCELLED,
    )
    response = api_client.get(f"/api/properties/{listing.pk}/booked-dates/")
    assert response.status_code == 200
    assert response.data == [{"check_in": days_from_now(5), "check_out": days_from_now(7)}]


# --- Expiring unpaid bookings ---------------------------------------------


def make_aged_booking(guest, listing, minutes_old, **kwargs):
    booking = Booking.objects.create(
        guest=guest,
        property=listing,
        check_in=days_from_now(10),
        check_out=days_from_now(12),
        total_price="200.00",
        **kwargs,
    )
    # created_at is auto_now_add, so backdate it with an update.
    Booking.objects.filter(pk=booking.pk).update(created_at=timezone.now() - timedelta(minutes=minutes_old))
    return booking


@pytest.mark.django_db
def test_expire_cancels_only_old_unpaid_pending_bookings(guest, listing, make_property, settings):
    from apps.payments.models import Payment

    from .services import expire_unpaid_bookings

    settings.BOOKING_PAYMENT_WINDOW_MINUTES = 60
    other = make_property(title="Other")
    stale = make_aged_booking(guest, listing, minutes_old=90)
    stale_with_failed_payment = make_aged_booking(guest, make_property(title="Third"), minutes_old=90)
    Payment.objects.create(booking=stale_with_failed_payment, amount="200", currency="usd")
    fresh = make_aged_booking(guest, other, minutes_old=10)
    paid = make_aged_booking(guest, make_property(title="Paid"), minutes_old=90)
    Payment.objects.create(booking=paid, amount="200", currency="usd", status=Payment.Status.COMPLETED)
    confirmed = make_aged_booking(guest, make_property(title="Conf"), minutes_old=90, status=Booking.Status.CONFIRMED)

    assert expire_unpaid_bookings() == 2

    statuses = {b.pk: b.status for b in Booking.objects.all()}
    assert statuses[stale.pk] == Booking.Status.CANCELLED
    assert statuses[stale_with_failed_payment.pk] == Booking.Status.CANCELLED
    assert statuses[fresh.pk] == Booking.Status.PENDING
    assert statuses[paid.pk] == Booking.Status.PENDING
    assert statuses[confirmed.pk] == Booking.Status.CONFIRMED
    assert Payment.objects.get(booking=stale_with_failed_payment).status == Payment.Status.FAILED


@pytest.mark.django_db
def test_expire_command_runs(guest, listing):
    from io import StringIO

    from django.core.management import call_command

    make_aged_booking(guest, listing, minutes_old=600)
    out = StringIO()
    call_command("expire_unpaid_bookings", stdout=out)
    assert "Cancelled 1 unpaid booking(s)" in out.getvalue()
