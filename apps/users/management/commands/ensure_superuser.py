import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Create an admin from DJANGO_SUPERUSER_EMAIL and DJANGO_SUPERUSER_PASSWORD if it doesn't exist yet. "
        "Safe to run on every start; does nothing when the variables are unset or the user exists."
    )

    def handle(self, *args, **options):
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "").strip()
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")
        if not email or not password:
            self.stdout.write("ensure_superuser: DJANGO_SUPERUSER_EMAIL/PASSWORD not set, skipping.")
            return

        User = get_user_model()
        if User.objects.filter(email__iexact=email).exists():
            # Never overwrite an existing account's password from the environment.
            self.stdout.write(f"ensure_superuser: {email} already exists.")
            return
        User.objects.create_superuser(email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f"ensure_superuser: created admin {email}."))
