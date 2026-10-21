from datetime import timedelta

import pytest
from django.utils import timezone

from apps.bookings.models import Booking

from .models import Review

LIST_URL = "/api/reviews/"


def days_from_now(n):
    return timezone.localdate() + timedelta(days=n)


@pytest.fixture
def listing(make_property):
    return make_property()


@pytest.fixture
def make_booking(guest, listing):
    def _make_booking(check_in=-5, check_out=-2, status=Booking.Status.CONFIRMED, **kwargs):
        defaults = {"guest": guest, "property": listing, "total_price": "300.00"}
        return Booking.objects.create(
            **{**defaults, **kwargs},
            check_in=days_from_now(check_in),
            check_out=days_from_now(check_out),
            status=status,
        )

    return _make_booking


@pytest.fixture
def past_stay(make_booking):
    return make_booking()


def review(client, booking, rating=5, comment="Great stay!"):
    return client.post(LIST_URL, {"booking": booking.pk, "rating": rating, "comment": comment}, format="json")


# --- Creating reviews -----------------------------------------------------


@pytest.mark.django_db
def test_guest_can_review_completed_stay(api_client, guest, past_stay):
    api_client.force_authenticate(guest)
    response = review(api_client, past_stay)
    assert response.status_code == 201
    created = Review.objects.get()
    assert created.author == guest
    assert created.property == past_stay.property


@pytest.mark.django_db
def test_only_one_review_per_stay(api_client, guest, past_stay):
    api_client.force_authenticate(guest)
    assert review(api_client, past_stay).status_code == 201
    assert review(api_client, past_stay).status_code == 400


@pytest.mark.django_db
def test_cannot_review_before_stay_ends(api_client, guest, make_booking):
    api_client.force_authenticate(guest)
    ongoing = make_booking(check_in=-1, check_out=2)
    assert review(api_client, ongoing).status_code == 400


@pytest.mark.django_db
@pytest.mark.parametrize("status", [Booking.Status.PENDING, Booking.Status.CANCELLED])
def test_cannot_review_unconfirmed_stay(api_client, guest, make_booking, status):
    api_client.force_authenticate(guest)
    assert review(api_client, make_booking(status=status)).status_code == 400


@pytest.mark.django_db
def test_cannot_review_someone_elses_stay(api_client, past_stay, make_user):
    api_client.force_authenticate(make_user())
    response = review(api_client, past_stay)
    assert response.status_code == 400
    assert not Review.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("rating", [0, 6])
def test_rating_must_be_1_to_5(api_client, guest, past_stay, rating):
    api_client.force_authenticate(guest)
    assert review(api_client, past_stay, rating=rating).status_code == 400


@pytest.mark.django_db
def test_anonymous_cannot_review(api_client, past_stay):
    assert review(api_client, past_stay).status_code == 401


# --- Reading, editing, deleting -------------------------------------------


@pytest.mark.django_db
def test_reviews_are_public_and_filterable(api_client, guest, past_stay, make_property, make_booking):
    other_listing = make_property(title="Other")
    Review.objects.create(booking=past_stay, property=past_stay.property, author=guest, rating=4)
    other_stay = make_booking(property=other_listing)
    Review.objects.create(booking=other_stay, property=other_listing, author=guest, rating=2)

    assert api_client.get(LIST_URL).data["count"] == 2
    results = api_client.get(LIST_URL, {"property": other_listing.pk}).data["results"]
    assert [r["rating"] for r in results] == [2]


@pytest.mark.django_db
def test_author_can_edit_and_delete(api_client, guest, past_stay):
    api_client.force_authenticate(guest)
    review_id = review(api_client, past_stay).data["id"]

    response = api_client.patch(f"{LIST_URL}{review_id}/", {"rating": 3}, format="json")
    assert response.status_code == 200
    assert response.data["rating"] == 3
    assert api_client.delete(f"{LIST_URL}{review_id}/").status_code == 204


@pytest.mark.django_db
def test_others_cannot_edit_or_delete(api_client, guest, past_stay, make_user):
    created = Review.objects.create(booking=past_stay, property=past_stay.property, author=guest, rating=5)
    api_client.force_authenticate(make_user())
    assert api_client.patch(f"{LIST_URL}{created.pk}/", {"rating": 1}, format="json").status_code == 403
    assert api_client.delete(f"{LIST_URL}{created.pk}/").status_code == 403


@pytest.mark.django_db
def test_booking_cannot_be_changed_on_edit(api_client, guest, past_stay, make_booking):
    created = Review.objects.create(booking=past_stay, property=past_stay.property, author=guest, rating=5)
    other_stay = make_booking()
    api_client.force_authenticate(guest)
    api_client.patch(f"{LIST_URL}{created.pk}/", {"booking": other_stay.pk}, format="json")
    created.refresh_from_db()
    assert created.booking == past_stay


# --- Ratings on listings --------------------------------------------------


@pytest.mark.django_db
def test_listing_shows_average_rating(api_client, guest, listing, make_booking, make_user):
    Review.objects.create(booking=make_booking(), property=listing, author=guest, rating=5)
    other = make_user()
    Review.objects.create(booking=make_booking(guest=other), property=listing, author=other, rating=4)

    data = api_client.get(f"/api/properties/{listing.pk}/").data
    assert data["average_rating"] == 4.5
    assert data["review_count"] == 2


@pytest.mark.django_db
def test_listing_without_reviews(api_client, listing):
    data = api_client.get(f"/api/properties/{listing.pk}/").data
    assert data["average_rating"] is None
    assert data["review_count"] == 0
