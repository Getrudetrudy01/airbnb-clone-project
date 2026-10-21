import pytest
from django.core.cache import cache
from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def _clear_cache():
    # Throttle counters live in the cache; reset them so tests don't affect each other.
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture(autouse=True)
def _fast_password_hasher(settings):
    # Production hashers are deliberately slow; tests don't need that.
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@pytest.fixture
def make_user(db):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    counter = iter(range(1, 10_000))

    def _make_user(role="guest", **kwargs):
        kwargs.setdefault("email", f"user{next(counter)}@example.com")
        return User.objects.create_user(password="Tr1cky-Passw0rd!", role=role, **kwargs)

    return _make_user


@pytest.fixture
def host(make_user):
    return make_user(role="host")


@pytest.fixture
def guest(make_user):
    return make_user(role="guest")


@pytest.fixture
def make_property(host):
    from apps.properties.models import Property

    def _make_property(**kwargs):
        defaults = {
            "host": host,
            "title": "Cosy flat",
            "description": "A lovely place to stay.",
            "address": "1 Main Street",
            "city": "Nairobi",
            "country": "Kenya",
            "price_per_night": "100.00",
            "max_guests": 4,
        }
        return Property.objects.create(**{**defaults, **kwargs})

    return _make_property


@pytest.fixture(autouse=True)
def _plain_static_storage(settings):
    # The production manifest storage needs `collectstatic` first; tests don't.
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
