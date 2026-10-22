# Deploying to Render

Render runs one **web service** (Django serving the API, the admin and the built React app on the same domain) and a **PostgreSQL** database. Both are described in [`render.yaml`](../render.yaml), so Render can create them together.

```
 browser ──▶ keyhouse  (web service, Docker, free plan)
              ├─ /          React app
              ├─ /api/...   Django REST API ──────▶ Stripe
              └─ /admin/    Django admin
                    │
                    ▼
             keyhouse-db  (PostgreSQL, free plan)
```

Every time the service starts, [`scripts/start.sh`](../scripts/start.sh) runs migrations, creates the admin account if it doesn't exist yet, optionally loads demo data, then starts Gunicorn. Running it again changes nothing, so restarts are safe.

## Before you start

- CI is green on `main` (Actions tab on GitHub).
- A Render account. Signing up with GitHub is easiest, because Render then sees your repositories.
- Optional now, needed later: your Stripe **test** secret key (`sk_test_…`).

## 1. Create everything from the Blueprint

1. In Render: **New → Blueprint**.
2. Connect **Getrudetrudy01/airbnb-clone-project** and pick the `main` branch. Render reads `render.yaml` and lists two resources: `keyhouse` (web service) and `keyhouse-db` (PostgreSQL).
3. Render asks for the variables marked as secrets:

   | Variable | What to enter |
   |---|---|
   | `DJANGO_SUPERUSER_EMAIL` | The email you'll use to log in to `/admin/` |
   | `DJANGO_SUPERUSER_PASSWORD` | A strong password for that account |
   | `STRIPE_SECRET_KEY` | Your `sk_test_…` key, or leave empty for now |
   | `STRIPE_WEBHOOK_SECRET` | Leave empty. You'll get it in step 4. |

   `SECRET_KEY` isn't in this list: Render generates a random one for you.
4. Click **Apply**. The first build takes about 5–10 minutes, because it builds the React app and then the Python image. Follow it in the service's **Logs** tab.

**Check it worked:** open `https://<service-name>.onrender.com/api/health/`. It should show `{"status":"ok"}`. Then open the home page and log in at `/admin/` with the account from step 3.

> If Render added a suffix to the name (e.g. `keyhouse-ab12`), use the URL shown at the top of the service page.

## 2. Optional: demo data

For a portfolio or demo site: service → **Environment** → set `SEED_DEMO` to `True` → **Save, rebuild and deploy**. The next start creates 12 listings, demo hosts and guests (password `Keyhouse-demo-2026`). Set it back to `False` afterwards. It won't create duplicates either way.

Don't do this on a site with real users.

## 3. Keep uploaded photos

Free Render services have no permanent disk, so photos uploaded by hosts disappear whenever the service restarts or redeploys. Store them in a bucket instead. Cloudflare R2 has a free tier:

1. In Cloudflare: **R2 → Create bucket**, e.g. `keyhouse-media`.
2. **R2 → Manage API tokens → Create API token** with *Object Read & Write* on that bucket. Copy the access key ID and secret.
3. Optional but recommended: in the bucket's **Settings**, enable public access (the `r2.dev` URL) so photo links don't expire.
4. In Render → `keyhouse` → **Environment**, add:

   | Variable | Value |
   |---|---|
   | `AWS_STORAGE_BUCKET_NAME` | `keyhouse-media` |
   | `AWS_ACCESS_KEY_ID` | from step 2 |
   | `AWS_SECRET_ACCESS_KEY` | from step 2 |
   | `AWS_S3_ENDPOINT_URL` | `https://<account-id>.r2.cloudflarestorage.com` |
   | `AWS_S3_REGION_NAME` | `auto` |
   | `AWS_S3_CUSTOM_DOMAIN` | the bucket's public host, e.g. `pub-xxxx.r2.dev` (only if you did step 3) |

## 4. Payments (Stripe test mode)

1. Stripe dashboard (test mode) → **Developers → Webhooks → Add endpoint**.
2. Endpoint URL: `https://<your-service>.onrender.com/api/payments/webhook/`
3. Events: `checkout.session.completed`, `checkout.session.expired`, `checkout.session.async_payment_succeeded`, `checkout.session.async_payment_failed`.
4. Copy the signing secret (`whsec_…`) into `STRIPE_WEBHOOK_SECRET` on Render. Also set `STRIPE_SECRET_KEY` if you skipped it earlier.

## 5. Recommended settings

- **Deploy only after CI passes:** service → **Settings → Build & Deploy → Auto-Deploy** → *After CI Checks Pass*. A failing test then never reaches the live site.
- **HSTS:** once HTTPS works, set `SECURE_HSTS_SECONDS` to `31536000`.

## 6. Smoke test

- [ ] `/api/health/` returns `{"status":"ok"}`
- [ ] The home page lists stays (see step 2 if it's empty)
- [ ] Sign up, log in, and open `/trips` directly in a new tab
- [ ] Book a stay and pay with `4242 4242 4242 4242`, any future date, any CVC
- [ ] The trip turns **Confirmed** within a few seconds
- [ ] As a host, upload a photo, then **Manual Deploy → Restart service**, and check the photo is still there
- [ ] `/admin/` works

## What the free plan means

| Limit | Effect on Keyhouse |
|---|---|
| The service sleeps after about 15 minutes without visitors | The first visit afterwards takes up to a minute while it wakes. Fine for a demo, not for real users. |
| The free database has a time limit (see Render's pricing page) | Upgrade the database, or export your data before it expires. |
| No cron jobs | Not needed. Unpaid reservations stop holding dates after `BOOKING_PAYMENT_WINDOW_MINUTES` (60) by themselves. The `expire_unpaid_bookings` command only tidies their stored status; on a paid plan you can add it as a Render Cron Job (`python manage.py expire_unpaid_bookings`, every 15 minutes). |
| No permanent disk | Use a bucket for photos (step 3). |

Upgrading the web service to a paid instance type removes the sleep.

## Using your own domain

Service → **Settings → Custom Domains** → add it and follow the DNS instructions. Then set:

| Variable | Value |
|---|---|
| `ALLOWED_HOSTS` | `keyhouse.example.com` |
| `CSRF_TRUSTED_ORIGINS` | `https://keyhouse.example.com` |
| `FRONTEND_URL` | `https://keyhouse.example.com` |

Update the Stripe webhook URL to the new domain as well.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| Deploy fails with `no such file or directory: scripts/start.sh` | The Blueprint is pointing at an old branch. Use `main`. |
| Health check keeps failing | Read the **Logs** tab. A crash during `migrate` usually means `DATABASE_URL` isn't linked: check the database exists and the variable comes from it. |
| `Bad Request (400)` | A custom domain that's missing from `ALLOWED_HOSTS`. |
| `CSRF verification failed` on `/admin/` | Add the site's `https://` origin to `CSRF_TRUSTED_ORIGINS`. |
| Can't log in to `/admin/` | `DJANGO_SUPERUSER_*` were empty on the first start. Set them and restart. The account is only created if it doesn't exist. |
| Payments say "isn't set up on this server yet" | `STRIPE_SECRET_KEY` is missing. |
| Trips stay "Awaiting payment" after paying | The Stripe webhook URL or `STRIPE_WEBHOOK_SECRET` is wrong. Stripe's webhook page shows failed deliveries. |
| Photos vanish after a while | No bucket configured (step 3). |
| Out-of-memory restarts | Lower `WEB_CONCURRENCY` to `1`. |
