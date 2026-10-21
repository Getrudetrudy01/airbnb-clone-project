import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_create_user_defaults_to_guest():
    user = User.objects.create_user(email="Guest@Example.com", password="s3cret-pass")
    assert user.email == "Guest@example.com"
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
