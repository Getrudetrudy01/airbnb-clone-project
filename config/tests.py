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
