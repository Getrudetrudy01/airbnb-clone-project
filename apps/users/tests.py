import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_create_user_defaults_to_guest():
    user = User.objects.create_user(email="Guest@Example.com", password="s3cret-pass")
    assert user.email == "guest@example.com"
    assert user.role == User.Role.GUEST
    assert user.check_password("s3cret-pass")
    assert not user.is_staff


@pytest.mark.django_db
def test_create_user_requires_email():
    with pytest.raises(ValueError):
        User.objects.create_user(email="", password="x")


@pytest.mark.django_db
def test_create_superuser_is_admin():
    admin = User.objects.create_superuser(email="admin@example.com", password="s3cret-pass")
    assert admin.is_staff and admin.is_superuser
    assert admin.role == User.Role.ADMIN


# --- API -------------------------------------------------------------------

REGISTER_URL = "/api/auth/register/"
LOGIN_URL = "/api/auth/login/"
REFRESH_URL = "/api/auth/refresh/"
ME_URL = "/api/users/me/"

STRONG_PASSWORD = "Tr1cky-Passw0rd!"


@pytest.fixture
def user():
    return User.objects.create_user(email="jane@example.com", password=STRONG_PASSWORD, first_name="Jane")


def login(client, email, password=STRONG_PASSWORD):
    return client.post(LOGIN_URL, {"email": email, "password": password}, format="json")


@pytest.mark.django_db
def test_register_creates_guest_by_default(api_client):
    response = api_client.post(REGISTER_URL, {"email": "new@example.com", "password": STRONG_PASSWORD}, format="json")
    assert response.status_code == 201
    assert response.data["role"] == "guest"
    assert "password" not in response.data
    assert User.objects.get(email="new@example.com").check_password(STRONG_PASSWORD)


@pytest.mark.django_db
def test_register_as_host(api_client):
    payload = {"email": "host@example.com", "password": STRONG_PASSWORD, "role": "host"}
    response = api_client.post(REGISTER_URL, payload, format="json")
    assert response.status_code == 201
    assert response.data["role"] == "host"


@pytest.mark.django_db
def test_register_cannot_create_admin(api_client):
    payload = {"email": "sneaky@example.com", "password": STRONG_PASSWORD, "role": "admin"}
    response = api_client.post(REGISTER_URL, payload, format="json")
    assert response.status_code == 400
    assert not User.objects.filter(email="sneaky@example.com").exists()


@pytest.mark.django_db
def test_register_rejects_weak_password(api_client):
    response = api_client.post(REGISTER_URL, {"email": "weak@example.com", "password": "123"}, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_register_rejects_duplicate_email(api_client, user):
    response = api_client.post(REGISTER_URL, {"email": user.email, "password": STRONG_PASSWORD}, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_login_returns_tokens(api_client, user):
    response = login(api_client, user.email)
    assert response.status_code == 200
    assert {"access", "refresh"} <= response.data.keys()


@pytest.mark.django_db
def test_login_wrong_password(api_client, user):
    response = login(api_client, user.email, password="wrong")
    assert response.status_code == 401


@pytest.mark.django_db
def test_refresh_returns_new_access_token(api_client, user):
    refresh = login(api_client, user.email).data["refresh"]
    response = api_client.post(REFRESH_URL, {"refresh": refresh}, format="json")
    assert response.status_code == 200
    assert "access" in response.data


@pytest.mark.django_db
def test_me_requires_auth(api_client):
    assert api_client.get(ME_URL).status_code == 401


@pytest.mark.django_db
def test_me_returns_profile(api_client, user):
    token = login(api_client, user.email).data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    response = api_client.get(ME_URL)
    assert response.status_code == 200
    assert response.data["email"] == user.email


@pytest.mark.django_db
def test_me_update_ignores_read_only_fields(api_client, user):
    api_client.force_authenticate(user)
    response = api_client.patch(ME_URL, {"first_name": "Janet", "role": "admin", "email": "x@x.com"}, format="json")
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.first_name == "Janet"
    assert user.role == User.Role.GUEST
    assert user.email == "jane@example.com"


@pytest.mark.django_db
def test_login_is_rate_limited(api_client, user):
    statuses = [login(api_client, user.email, password="wrong").status_code for _ in range(11)]
    assert statuses[-1] == 429


# --- Email case-insensitivity ---------------------------------------------


@pytest.mark.django_db
def test_register_lowercases_email(api_client):
    response = api_client.post(REGISTER_URL, {"email": "Mixed@Example.COM", "password": STRONG_PASSWORD}, format="json")
    assert response.status_code == 201
    assert response.data["email"] == "mixed@example.com"


@pytest.mark.django_db
def test_register_rejects_duplicate_email_in_other_case(api_client, user):
    response = api_client.post(REGISTER_URL, {"email": "JANE@example.com", "password": STRONG_PASSWORD}, format="json")
    assert response.status_code == 400
    assert User.objects.count() == 1


@pytest.mark.django_db
def test_login_is_case_insensitive(api_client, user):
    assert login(api_client, "Jane@Example.com").status_code == 200
