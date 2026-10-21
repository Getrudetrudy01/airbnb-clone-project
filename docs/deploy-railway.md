# Deploying to Railway

One Railway **web service** runs Django, which serves both the API and the built React app on the same domain. A **MySQL** database and a small **cron service** sit alongside it.

```
            ┌──────────────── Railway project ────────────────┐
 browser ──▶│  web  (Dockerfile, railway.json)                 │
            │   ├─ /            React app (frontend/dist)      │
            │   ├─ /api/...     Django REST API                │──▶ Stripe
            │   └─ /admin/      Django admin                   │
            │        │                                          │
            │        ▼                                          │
            │  MySQL           cron (railway.cron.json)         │
            │                  expire_unpaid_bookings /15 min   │
            └───────────────────────────────────────────────────┘
```

What's already in the repo:

| File | What it does |
|---|---|
| `Dockerfile` | Builds the React app, then the Django image that serves it |
| `railway.json` | Web service: runs `migrate` before each deploy, health check on `/api/health/` |
| `railway.cron.json` | Cron service: runs `expire_unpaid_bookings` every 15 minutes |

## 1. Create the project and database

1. In Railway, **New Project → Deploy from GitHub repo** and pick this repository. Railway finds `railway.json` and builds the Dockerfile. The first deploy will fail until the variables below are set; that's expected.
2. In the project, **+ New → Database → MySQL**.
3. Rename the GitHub service to `web` (Settings → Service name). The variable references below assume that name.

## 2. Set the web service's variables

Open the `web` service → **Variables** and add:

| Variable | Value |
|---|---|
| `SECRET_KEY` | A long random string. Generate one with `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `DEBUG` | `False` |
| `DATABASE_URL` | `${{MySQL.MYSQL_URL}}` (Railway fills in the real URL) |

You don't need to set `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` or `FRONTEND_URL` for the Railway domain: the app reads `RAILWAY_PUBLIC_DOMAIN`, which Railway provides, and trusts it automatically.

Then **Settings → Networking → Generate Domain**. Railway redeploys.

**Check it worked:** open `https://<your-domain>/api/health/`. It should say `{"status":"ok"}`, and `https://<your-domain>/` should show the site.

## 3. Create an admin account (and optional demo data)

With the [Railway CLI](https://docs.railway.com/guides/cli) installed and logged in:

```bash
railway link            # pick the project and the web service
railway ssh             # opens a shell inside the running container
python manage.py createsuperuser
python manage.py seed_demo   # optional: only for a demo site, never alongside real users
exit
```

## 4. Keep uploaded photos

Containers start from a clean disk on every deploy, so photos need somewhere permanent. Pick one:

**Option A: Railway volume (quickest, no extra account)**

1. `web` service → right-click → **Attach volume**, mount path `/app/media`.
2. Add variables `SERVE_MEDIA` = `True` and `RAILWAY_RUN_UID` = `0`. Volumes mount as root, so the container has to run as root to write to it.

**Option B: S3-compatible bucket (better for real traffic)**

Works with Cloudflare R2 (generous free tier), AWS S3 and similar. Create a bucket and an access key, then add:

| Variable | Example |
|---|---|
| `AWS_STORAGE_BUCKET_NAME` | `keyhouse-media` |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | From the provider |
| `AWS_S3_ENDPOINT_URL` | R2: `https://<account-id>.r2.cloudflarestorage.com` (leave unset for AWS) |
| `AWS_S3_REGION_NAME` | AWS: e.g. `eu-west-1`; R2: `auto` |
| `AWS_S3_CUSTOM_DOMAIN` | Optional: the bucket's public domain. Without it, photo links are signed and expire after an hour. |

## 5. Add the cron service

Unpaid reservations hold their dates until this job releases them.

1. **+ New → GitHub Repo** → the same repository. Name it `cron`.
2. **Settings → Config-as-code → Config file path**: `railway.cron.json`.
3. **Variables**: `SECRET_KEY` = `${{web.SECRET_KEY}}`, `DEBUG` = `False`, `DATABASE_URL` = `${{MySQL.MYSQL_URL}}`.

Its logs show `Cancelled N unpaid booking(s)…` every 15 minutes.

## 6. Payments (Stripe test mode)

1. In the [Stripe dashboard](https://dashboard.stripe.com/test/apikeys) (test mode), copy the **secret key**.
2. **Developers → Webhooks → Add endpoint**: URL `https://<your-domain>/api/payments/webhook/`, events:
   `checkout.session.completed`, `checkout.session.expired`, `checkout.session.async_payment_succeeded`, `checkout.session.async_payment_failed`.
3. Add to the `web` service: `STRIPE_SECRET_KEY` = `sk_test_…` and `STRIPE_WEBHOOK_SECRET` = the endpoint's `whsec_…`.

## 7. Smoke test

- [ ] `/api/health/` returns `{"status":"ok"}`
- [ ] The home page lists stays (run `seed_demo` if the database is empty)
- [ ] Sign up, log in, and open `/trips` directly in a new tab (page routes should load, not 404)
- [ ] Book a stay and pay with `4242 4242 4242 4242`, any future date, any CVC
- [ ] The trip turns **Confirmed** within a few seconds (Stripe webhook → your API)
- [ ] As a host, upload a photo, redeploy, and check the photo is still there
- [ ] `/admin/` loads and you can log in

Once everything works over HTTPS, raise `SECURE_HSTS_SECONDS` to `31536000`.

## Using your own domain

Add it under **Settings → Networking → Custom Domain**, then set:

| Variable | Value |
|---|---|
| `ALLOWED_HOSTS` | `keyhouse.example.com` |
| `CSRF_TRUSTED_ORIGINS` | `https://keyhouse.example.com` |
| `FRONTEND_URL` | `https://keyhouse.example.com` (where Stripe sends guests back) |

Update the Stripe webhook URL to the new domain too.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `Bad Request (400)` on every page | The domain isn't in `ALLOWED_HOSTS`. Custom domains must be added by hand. |
| Deploy fails at the health check | Check the deploy logs. Usually `DATABASE_URL` or `SECRET_KEY` is missing. |
| `CSRF verification failed` on `/admin/` | Add the site's `https://` origin to `CSRF_TRUSTED_ORIGINS`. |
| Payments say "isn't set up on this server yet" | `STRIPE_SECRET_KEY` is missing on the `web` service. |
| Bookings stay "Awaiting payment" after paying | The Stripe webhook URL or `STRIPE_WEBHOOK_SECRET` is wrong. Stripe's webhook page shows failed deliveries. |
| Photos vanish after a deploy | No volume or bucket configured (step 4). |
