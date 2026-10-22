import io
from datetime import timedelta

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from PIL import Image

from apps.bookings.models import Booking

from .models import Property

LIST_URL = "/api/properties/"


def detail_url(pk):
    return f"/api/properties/{pk}/"


def new_listing(**overrides):
    payload = {
        "title": "Beach house",
        "description": "Sea views.",
        "address": "2 Ocean Road",
        "city": "Mombasa",
        "country": "Kenya",
        "price_per_night": "150.00",
        "max_guests": 6,
    }
    return {**payload, **overrides}


def png_file(name="photo.png"):
    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), "red").save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


# --- Read access ---------------------------------------------------------


@pytest.mark.django_db
def test_anyone_can_list_and_view(api_client, make_property):
    listing = make_property()
    assert api_client.get(LIST_URL).data["count"] == 1
    response = api_client.get(detail_url(listing.pk))
    assert response.status_code == 200
    assert response.data["host"] == {"id": listing.host.pk, "name": listing.host.display_name}
    assert listing.host.email not in str(response.data)


# --- Create / update / delete permissions --------------------------------


@pytest.mark.django_db
def test_host_can_create_listing(api_client, host):
    api_client.force_authenticate(host)
    response = api_client.post(LIST_URL, new_listing(), format="json")
    assert response.status_code == 201
    assert Property.objects.get().host == host


@pytest.mark.django_db
def test_guest_cannot_create_listing(api_client, guest):
    api_client.force_authenticate(guest)
    assert api_client.post(LIST_URL, new_listing(), format="json").status_code == 403


@pytest.mark.django_db
def test_anonymous_cannot_create_listing(api_client):
    assert api_client.post(LIST_URL, new_listing(), format="json").status_code == 401


@pytest.mark.django_db
def test_host_field_cannot_be_spoofed(api_client, host, make_user):
    other = make_user(role="host")
    api_client.force_authenticate(host)
    api_client.post(LIST_URL, new_listing(host=other.pk), format="json")
    assert Property.objects.get().host == host


@pytest.mark.django_db
def test_owner_can_update_and_delete(api_client, make_property):
    listing = make_property()
    api_client.force_authenticate(listing.host)
    response = api_client.patch(detail_url(listing.pk), {"price_per_night": "120.00"}, format="json")
    assert response.status_code == 200
    assert response.data["price_per_night"] == "120.00"
    assert api_client.delete(detail_url(listing.pk)).status_code == 204


@pytest.mark.django_db
def test_other_host_cannot_update_or_delete(api_client, make_property, make_user):
    listing = make_property()
    api_client.force_authenticate(make_user(role="host"))
    assert api_client.patch(detail_url(listing.pk), {"title": "Mine now"}, format="json").status_code == 403
    assert api_client.delete(detail_url(listing.pk)).status_code == 403


@pytest.mark.django_db
def test_price_must_be_positive(api_client, host):
    api_client.force_authenticate(host)
    assert api_client.post(LIST_URL, new_listing(price_per_night="0"), format="json").status_code == 400


# --- Filtering / search ---------------------------------------------------


@pytest.mark.django_db
def test_filter_by_city_price_and_guests(api_client, make_property):
    make_property(title="Cheap", city="Nairobi", price_per_night="50.00", max_guests=2)
    make_property(title="Pricey", city="Nairobi", price_per_night="300.00", max_guests=8)
    make_property(title="Elsewhere", city="Kisumu", price_per_night="80.00", max_guests=4)

    def titles(params):
        return {p["title"] for p in api_client.get(LIST_URL, params).data["results"]}

    assert titles({"city": "nair"}) == {"Cheap", "Pricey"}
    assert titles({"max_price": 100}) == {"Cheap", "Elsewhere"}
    assert titles({"min_price": 100}) == {"Pricey"}
    assert titles({"guests": 4}) == {"Pricey", "Elsewhere"}
    assert titles({"search": "kisumu"}) == {"Elsewhere"}


@pytest.mark.django_db
def test_filter_by_availability(api_client, make_property, guest):
    booked = make_property(title="Booked")
    make_property(title="Free")
    start = timezone.localdate() + timedelta(days=10)
    Booking.objects.create(
        guest=guest, property=booked, check_in=start, check_out=start + timedelta(days=3), total_price="300.00"
    )

    params = {"check_in": start + timedelta(days=1), "check_out": start + timedelta(days=5)}
    results = api_client.get(LIST_URL, params).data["results"]
    assert [p["title"] for p in results] == ["Free"]


@pytest.mark.django_db
def test_filter_by_host(api_client, make_property, make_user):
    other_host = make_user(role="host")
    make_property(title="Mine")
    make_property(title="Theirs", host=other_host)
    results = api_client.get(LIST_URL, {"host": other_host.pk}).data["results"]
    assert [p["title"] for p in results] == ["Theirs"]


@pytest.mark.django_db
def test_availability_filter_needs_both_dates(api_client):
    assert api_client.get(LIST_URL, {"check_in": "2030-01-01"}).status_code == 400


# --- Images ---------------------------------------------------------------


@pytest.fixture
def media_root(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    return tmp_path


@pytest.mark.django_db
def test_owner_can_upload_and_delete_image(api_client, make_property, media_root):
    listing = make_property()
    api_client.force_authenticate(listing.host)

    response = api_client.post(f"{detail_url(listing.pk)}images/", {"image": png_file()}, format="multipart")
    assert response.status_code == 201
    image_id = response.data["id"]
    assert listing.images.count() == 1

    response = api_client.delete(f"{detail_url(listing.pk)}images/{image_id}/")
    assert response.status_code == 204
    assert listing.images.count() == 0


@pytest.mark.django_db
def test_non_owner_cannot_upload_image(api_client, make_property, make_user, media_root):
    listing = make_property()
    api_client.force_authenticate(make_user(role="host"))
    response = api_client.post(f"{detail_url(listing.pk)}images/", {"image": png_file()}, format="multipart")
    assert response.status_code == 403


@pytest.mark.django_db
def test_upload_rejects_non_image(api_client, make_property, media_root):
    listing = make_property()
    api_client.force_authenticate(listing.host)
    bogus = SimpleUploadedFile("notes.png", b"not an image", content_type="image/png")
    response = api_client.post(f"{detail_url(listing.pk)}images/", {"image": bogus}, format="multipart")
    assert response.status_code == 400


# --- Shared demo host is read-only ------------------------------------------


@pytest.mark.django_db
def test_demo_host_cannot_change_listings(api_client, make_property):
    from django.contrib.auth import get_user_model

    from apps.users.demo import DEMO_LOGINS

    demo_host = get_user_model().objects.create_user(email=DEMO_LOGINS["host"], password="x", role="host")
    listing = make_property(host=demo_host)
    api_client.force_authenticate(demo_host)

    assert api_client.post(LIST_URL, new_listing(), format="json").status_code == 403
    assert api_client.patch(detail_url(listing.pk), {"title": "Defaced"}, format="json").status_code == 403
    assert api_client.delete(detail_url(listing.pk)).status_code == 403
    response = api_client.post(f"{detail_url(listing.pk)}images/", {"image": png_file()}, format="multipart")
    assert response.status_code == 403
    assert "demo" in response.data["detail"]
    # Looking around still works.
    assert api_client.get(detail_url(listing.pk)).status_code == 200
