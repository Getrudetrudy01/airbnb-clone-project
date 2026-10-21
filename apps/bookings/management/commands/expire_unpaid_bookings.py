from django.conf import settings
from django.core.management.base import BaseCommand

from apps.bookings.services import expire_unpaid_bookings


class Command(BaseCommand):
    help = "Cancel pending bookings that weren't paid within BOOKING_PAYMENT_WINDOW_MINUTES. Run on a schedule."

    def handle(self, *args, **options):
        count = expire_unpaid_bookings()
        self.stdout.write(
            f"Cancelled {count} unpaid booking(s) older than {settings.BOOKING_PAYMENT_WINDOW_MINUTES} minutes."
        )
