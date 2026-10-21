import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.bookings.models import Booking
from apps.properties.models import Property
from apps.reviews.models import Review

User = get_user_model()

DEMO_DOMAIN = "demo.keyhouse.test"
DEMO_PASSWORD = "Keyhouse-demo-2026"

HOSTS = [
    ("amara", "Amara", "Okafor"),
    ("tomas", "Tomás", "Ribeiro"),
    ("yuki", "Yuki", "Tanaka"),
    ("lena", "Lena", "Hoffmann"),
]

GUESTS = [
    ("guest", "Sam", "Mwangi"),
    ("priya", "Priya", "Nair"),
    ("jonah", "Jonah", "Clarke"),
    ("ines", "Inês", "Duarte"),
]

# (host, title, city, country, address, price, guests, description)
LISTINGS = [
    (
        "tomas",
        "Tiled flat above the tram line",
        "Lisbon",
        "Portugal",
        "Rua da Graça 41",
        "96.00",
        3,
        "Second-floor flat in Graça with original azulejo tiles in the hall and a narrow balcony over the 28 tram. "
        "The bedroom faces the courtyard, so nights are quiet. Five minutes' walk to the Senhora do Monte viewpoint.",
    ),
    (
        "amara",
        "Garden cottage in Kilimani",
        "Nairobi",
        "Kenya",
        "Argwings Kodhek Road",
        "74.00",
        2,
        "A one-room cottage at the back of our garden, under a jacaranda. Kitchenette, fast fibre, and a desk "
        "by the window. Yaya Centre and the Kilimani cafés are a ten-minute walk; Uber pickups are easy.",
    ),
    (
        "amara",
        "Beach house on the Nyali shore",
        "Mombasa",
        "Kenya",
        "Mount Kenya Road, Nyali",
        "185.00",
        8,
        "Four bedrooms opening onto a shaded veranda and a path straight to the sand. Our housekeeper comes "
        "in each morning. Best at high tide, when the reef pools fill up.",
    ),
    (
        "yuki",
        "Machiya townhouse near Kamogawa",
        "Kyoto",
        "Japan",
        "Shimogyo-ku, Kyoto",
        "210.00",
        4,
        "A restored wooden townhouse with tatami rooms, a small stone garden and a deep cypress bath. "
        "Futons are laid out each evening. Ten minutes on foot to Gion across the river.",
    ),
    (
        "lena",
        "Courtyard loft in Kreuzberg",
        "Berlin",
        "Germany",
        "Oranienstraße 18",
        "88.00",
        2,
        "Top-floor loft in a Hinterhof, with a skylight over the bed and a record player in the corner. "
        "U-Bahn Moritzplatz is around the corner. The building is old: four flights, no lift.",
    ),
    (
        "tomas",
        "Studio by the Ribeira steps",
        "Porto",
        "Portugal",
        "Escadas do Codeçal 7",
        "68.00",
        2,
        "Small, bright studio halfway up the stairs from the river, with a view across to the port cellars "
        "in Gaia. Steep walk home, but you'll never be short of a pastel de nata on the way.",
    ),
    (
        "lena",
        "Lakeside cabin near Hallstatt",
        "Hallstatt",
        "Austria",
        "Seestraße 112",
        "164.00",
        5,
        "Larch-clad cabin with its own jetty and a rowing boat. Wood stove, two bedrooms and a sleeping loft. "
        "The village is a twenty-minute walk along the shore; the last bus back leaves at seven.",
    ),
    (
        "yuki",
        "Quiet room in Nakameguro",
        "Tokyo",
        "Japan",
        "Kamimeguro, Meguro-ku",
        "112.00",
        2,
        "A calm one-bedroom on a side street off the canal, which is lined with cherry trees in early April. "
        "Two stops to Shibuya. Pocket Wi-Fi and a rice cooker included.",
    ),
    (
        "amara",
        "Forest lodge near Naivasha",
        "Naivasha",
        "Kenya",
        "Moi South Lake Road",
        "132.00",
        6,
        "Stone-and-timber lodge among acacias, with zebra often grazing on the lawn at breakfast. "
        "Fire pit, full kitchen and three bedrooms. Hell's Gate is twenty minutes by car.",
    ),
    (
        "tomas",
        "Whitewashed house in the Alfama",
        "Lisbon",
        "Portugal",
        "Beco do Carneiro 3",
        "142.00",
        5,
        "Three floors of a narrow house on a stepped alley, with a roof terrace that looks over the river. "
        "You'll hear fado from the bar below on weekends, until about midnight.",
    ),
    (
        "lena",
        "Altbau apartment in Prenzlauer Berg",
        "Berlin",
        "Germany",
        "Kollwitzstraße 60",
        "121.00",
        4,
        "High ceilings, herringbone floors and two bedrooms off a long hall. The Saturday market on "
        "Kollwitzplatz is right outside. Cot and high chair available on request.",
    ),
    (
        "yuki",
        "Onsen ryokan suite in Hakone",
        "Hakone",
        "Japan",
        "Gora, Ashigarashimo",
        "268.00",
        2,
        "Private suite with its own outdoor hot-spring bath on a cedar deck. Kaiseki dinner can be added "
        "when booking. On clear mornings Fuji shows up over the ridge.",
    ),
]

REVIEW_LINES = [
    (5, "Exactly as described, and spotless. We'd book it again tomorrow."),
    (5, "The host's notes on where to eat were better than any guidebook."),
    (4, "Lovely place. The stairs are real, so pack light."),
    (5, "Slept better here than at home. Very quiet at night."),
    (4, "Great location, kitchen is small but has everything you need."),
    (3, "Nice enough, though the Wi-Fi dropped a few times."),
    (5, "Check-in was easy and the view was the highlight of the trip."),
]


class Command(BaseCommand):
    help = "Create demo hosts, guests, listings, past stays and reviews. Safe to re-run with --reset."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete existing demo data first.")

    @transaction.atomic
    def handle(self, *args, reset=False, **options):
        demo_users = User.objects.filter(email__endswith=f"@{DEMO_DOMAIN}")
        if demo_users.exists():
            if not reset:
                self.stdout.write("Demo data already exists. Run with --reset to recreate it.")
                return
            demo_users.delete()  # Cascades to listings, bookings and reviews.

        rng = random.Random(7)
        hosts = {key: self._user(key, first, last, User.Role.HOST) for key, first, last in HOSTS}
        guests = [self._user(key, first, last, User.Role.GUEST) for key, first, last in GUESTS]

        today = timezone.localdate()
        for host_key, title, city, country, address, price, max_guests, description in LISTINGS:
            listing = Property.objects.create(
                host=hosts[host_key],
                title=title,
                description=description,
                address=address,
                city=city,
                country=country,
                price_per_night=Decimal(price),
                max_guests=max_guests,
            )
            # A few finished, reviewed stays so listings have ratings.
            start = today - timedelta(days=rng.randint(30, 50))
            for guest in rng.sample(guests, k=rng.randint(1, 3)):
                nights = rng.randint(2, 5)
                booking = Booking.objects.create(
                    guest=guest,
                    property=listing,
                    check_in=start,
                    check_out=start + timedelta(days=nights),
                    guests=1,
                    total_price=listing.price_per_night * nights,
                    status=Booking.Status.CONFIRMED,
                )
                rating, comment = rng.choice(REVIEW_LINES)
                Review.objects.create(booking=booking, property=listing, author=guest, rating=rating, comment=comment)
                start = booking.check_out + timedelta(days=rng.randint(1, 6))

        self.stdout.write(self.style.SUCCESS(f"Created {len(LISTINGS)} listings with past stays and reviews."))
        self.stdout.write(f"Log in as guest@{DEMO_DOMAIN} or amara@{DEMO_DOMAIN} (host), password: {DEMO_PASSWORD}")

    def _user(self, key, first, last, role):
        return User.objects.create_user(
            email=f"{key}@{DEMO_DOMAIN}", password=DEMO_PASSWORD, first_name=first, last_name=last, role=role
        )
