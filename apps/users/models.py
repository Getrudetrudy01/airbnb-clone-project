from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

from .demo import is_demo_email


class UserManager(BaseUserManager):
    """Manager for a user model that logs in with email instead of username."""

    use_in_migrations = True

    @classmethod
    def normalize_email(cls, email):
        # Treat Jane@Example.com and jane@example.com as the same account.
        return super().normalize_email(email).lower()

    def get_by_natural_key(self, email):
        # Used by login; makes it case-insensitive.
        return self.get(email__iexact=email)

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)
        if not extra_fields["is_staff"] or not extra_fields["is_superuser"]:
            raise ValueError("Superuser must have is_staff=True and is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        GUEST = "guest", "Guest"
        HOST = "host", "Host"
        ADMIN = "admin", "Admin"

    username = None
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.GUEST)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    @property
    def display_name(self):
        """Public-facing name: "Jane D." Never exposes the email address."""
        if self.first_name:
            initial = f" {self.last_name[0]}." if self.last_name else ""
            return f"{self.first_name}{initial}"
        return "Keyhouse member"

    @property
    def is_demo(self) -> bool:
        """One of the shared demo accounts from seed_demo."""
        return is_demo_email(self.email)

    @property
    def is_host(self):
        return self.role == self.Role.HOST
