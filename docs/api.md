# API reference

Interactive docs are served by the app itself: **Swagger UI** at `/api/docs/` (click **Authorize** and paste an access token to try protected endpoints), **ReDoc** at `/api/redoc/`, and the **OpenAPI schema** at `/api/schema/`.

## Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register/` | — | Create an account (`role`: `guest` or `host`) |
| POST | `/api/auth/login/` | — | Get `access` + `refresh` JWT tokens |
| POST | `/api/auth/refresh/` | — | Get a new access token from a refresh token |
| GET / POST | `/api/auth/demo/` | — | Whether demo login is available; log in as the demo `guest` or `host` |
| GET / PATCH | `/api/users/me/` | Bearer | View or update your profile |
| GET | `/api/properties/` | — | List listings (filters below) |
| POST | `/api/properties/` | Host | Create a listing |
| GET | `/api/properties/{id}/` | — | Listing details |
| PATCH / DELETE | `/api/properties/{id}/` | Owner | Update or delete a listing |
| POST | `/api/properties/{id}/images/` | Owner | Upload an image (multipart, max 5 MB) |
| DELETE | `/api/properties/{id}/images/{image_id}/` | Owner | Remove an image |
| GET | `/api/properties/{id}/booked-dates/` | — | Upcoming booked date ranges |
| GET | `/api/bookings/` | Bearer | Your bookings as guest and as host (`?status=`, `?property=`) |
| POST | `/api/bookings/` | Bearer | Book a property (`property`, `check_in`, `check_out`, `guests`) |
| GET | `/api/bookings/{id}/` | Guest or host | Booking details |
| POST | `/api/bookings/{id}/confirm/` | Host | Confirm a pending booking |
| POST | `/api/bookings/{id}/cancel/` | Guest or host | Cancel before check-in (refunds if paid) |
| GET | `/api/reviews/` | — | List reviews (`?property=`, `?rating=`) |
| POST | `/api/reviews/` | Guest | Review a finished, confirmed stay (`booking`, `rating` 1–5, `comment`) |
| PATCH / DELETE | `/api/reviews/{id}/` | Author | Edit or delete your review |
| POST | `/api/payments/checkout/` | Guest | Start Stripe Checkout for a booking; returns `checkout_url` |
| GET | `/api/payments/` | Bearer | Payments for your bookings (as guest or host) |
| POST | `/api/payments/webhook/` | Stripe signature | Stripe event receiver |

Send the access token as `Authorization: Bearer <token>`. Access tokens last 15 minutes and refresh tokens 7 days. Register and login are limited to 10 requests per minute.

**Listing filters:** `city`, `country`, `min_price`, `max_price`, `guests` (minimum capacity), `check_in` + `check_out` (only show available listings), `search` (title/description/location) and `ordering` (`price_per_night`, `average_rating`, `-created_at`, ...). Each listing includes `average_rating` and `review_count`.

**Booking rules:** check-in can't be in the past, stays are 1–90 nights, guest count can't exceed the listing's limit, hosts can't book their own listings, and dates can't overlap an existing pending or confirmed booking (check-out day is free for the next guest). The total price is calculated by the server.

## Testing payments locally

1. Create a free Stripe account and copy the **test** secret key into `STRIPE_SECRET_KEY` in `.env`.
2. Install the [Stripe CLI](https://docs.stripe.com/stripe-cli) and forward webhooks to your local server:
   ```bash
   stripe login
   stripe listen --forward-to localhost:8000/api/payments/webhook/
   ```
   Put the `whsec_...` secret it prints into `STRIPE_WEBHOOK_SECRET`, then restart the server.
3. Create a booking, `POST /api/payments/checkout/` with its id, open the returned `checkout_url` and pay with test card `4242 4242 4242 4242` (any future date, any CVC).

When Stripe reports the payment, the booking becomes **confirmed**. Cancelling a paid booking refunds it in full. Card details only ever go to Stripe.

## Releasing unpaid reservations

A pending booking that is not paid within `BOOKING_PAYMENT_WINDOW_MINUTES` (default 60) stops holding its dates automatically and is reported as cancelled; no scheduled job is needed for that. `python manage.py expire_unpaid_bookings` also updates the stored status of those bookings; run it on a schedule if your host supports cron.
