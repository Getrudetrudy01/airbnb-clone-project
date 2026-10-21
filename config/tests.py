from unittest import mock

import pytest
from django.db import OperationalError


@pytest.mark.django_db
def test_health_ok(api_client):
    response = api_client.get("/api/health/")
    assert response.status_code == 200
    assert response.data == {"status": "ok"}


@pytest.mark.django_db
def test_health_reports_database_down(api_client):
    with mock.patch("config.views.connection.ensure_connection", side_effect=OperationalError("down")):
        assert api_client.get("/api/health/").status_code == 503


@pytest.mark.django_db
def test_openapi_schema_generates(api_client):
    response = api_client.get("/api/schema/", {"format": "json"})
    assert response.status_code == 200
    paths = response.json()["paths"]
    for expected in ["/api/properties/", "/api/bookings/", "/api/reviews/", "/api/payments/checkout/"]:
        assert expected in paths


@pytest.mark.django_db
def test_swagger_ui_loads(api_client):
    assert api_client.get("/api/docs/").status_code == 200


# --- Serving the React app ------------------------------------------------


@pytest.fixture
def built_frontend(settings, tmp_path):
    (tmp_path / "index.html").write_text("<!doctype html><title>Keyhouse</title>")
    settings.FRONTEND_DIST = tmp_path
    return tmp_path


@pytest.mark.django_db
@pytest.mark.parametrize("path", ["/", "/trips", "/stays/3", "/hosting/listings/new"])
def test_page_routes_serve_the_app(client, built_frontend, path):
    response = client.get(path)
    assert response.status_code == 200
    assert b"<title>Keyhouse</title>" in response.content
    assert response["Cache-Control"] == "no-cache"


@pytest.mark.django_db
def test_api_routes_are_not_swallowed_by_the_app(client, built_frontend):
    response = client.get("/api/does-not-exist/")
    assert response.status_code == 404
    assert b"Keyhouse" not in response.content


@pytest.mark.django_db
def test_unbuilt_frontend_explains_itself(client, settings, tmp_path):
    settings.FRONTEND_DIST = tmp_path / "missing"
    response = client.get("/")
    assert response.status_code == 404
    assert b"npm run build" in response.content


@pytest.mark.django_db
def test_health_check_skips_https_redirect(client, settings):
    settings.SECURE_SSL_REDIRECT = True
    settings.SECURE_REDIRECT_EXEMPT = [r"^api/health/$"]
    assert client.get("/api/health/").status_code in (200, 503)
    assert client.get("/api/properties/").status_code == 301
