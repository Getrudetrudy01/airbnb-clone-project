"""
Django settings for the Airbnb Clone project.

All environment-specific values are read from environment variables
(or a local .env file). See .env.example for the full list.
"""

import re
from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# Hosting platforms announce the service's public hostname in an environment variable
# (Render: RENDER_EXTERNAL_HOSTNAME, Railway: RAILWAY_PUBLIC_DOMAIN). Trust it automatically
# so a fresh deploy works without setting ALLOWED_HOSTS by hand.
PUBLIC_HOSTNAME = env("RENDER_EXTERNAL_HOSTNAME", default="") or env("RAILWAY_PUBLIC_DOMAIN", default="")
if PUBLIC_HOSTNAME:
    ALLOWED_HOSTS.append(PUBLIC_HOSTNAME)
if env("RAILWAY_ENVIRONMENT_NAME", default=""):
    ALLOWED_HOSTS.append("healthcheck.railway.app")


# Application definition

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "django_filters",
    "corsheaders",
    "drf_spectacular",
]

LOCAL_APPS = [
    "apps.users",
    "apps.properties",
    "apps.bookings",
    "apps.reviews",
    "apps.payments",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
# Defaults to SQLite for quick local development. Set DATABASE_URL for MySQL or PostgreSQL,
# e.g. mysql://airbnb:airbnb@localhost:3306/airbnb or postgres://user:pass@host:5432/airbnb

DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
}
# Reuse database connections between requests instead of reconnecting every time.
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=60)
# Check a reused connection is still alive first; managed databases drop idle ones.
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True
if DATABASES["default"]["ENGINE"] == "django.db.backends.mysql":
    # MySQL's legacy "utf8" can't store emoji; utf8mb4 can.
    DATABASES["default"].setdefault("OPTIONS", {})["charset"] = "utf8mb4"


# Authentication

AUTH_USER_MODEL = "users.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Django REST Framework

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        # Session auth keeps the browsable API usable after logging in at /admin/.
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": env("ANON_THROTTLE_RATE", default="60/min"),
        "user": env("USER_THROTTLE_RATE", default="300/min"),
        "auth": env("AUTH_THROTTLE_RATE", default="10/min"),
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env.int("JWT_ACCESS_MINUTES", default=15)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.int("JWT_REFRESH_DAYS", default=7)),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Airbnb Clone API",
    "DESCRIPTION": "Listings, bookings, reviews and payments. Send `Authorization: Bearer <access token>`.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}


# Demo accounts

# "Try the demo" one-click login for the seed_demo accounts. It only works once those
# accounts exist, so sites without demo data are unaffected.
DEMO_LOGIN_ENABLED = env.bool("DEMO_LOGIN_ENABLED", default=True)


# Bookings

# Pending bookings that aren't paid within this window are cancelled by the
# `expire_unpaid_bookings` management command, freeing their dates.
BOOKING_PAYMENT_WINDOW_MINUTES = env.int("BOOKING_PAYMENT_WINDOW_MINUTES", default=60)


# Payments (Stripe). Leave the keys empty to disable payments.

STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", default="")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET", default="")
PAYMENTS_CURRENCY = env("PAYMENTS_CURRENCY", default="usd")
# Where Stripe sends the guest after checkout.
_default_frontend = f"https://{PUBLIC_HOSTNAME}" if PUBLIC_HOSTNAME else "http://localhost:3000"
FRONTEND_URL = env("FRONTEND_URL", default=_default_frontend).rstrip("/")


# CORS / CSRF: which browser origins may call the API.

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[FRONTEND_URL])
CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS", default=[f"https://{PUBLIC_HOSTNAME}"] if PUBLIC_HOSTNAME else []
)


# Internationalization

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# Static files

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    # WhiteNoise serves compressed, cache-busted static files without a separate web server.
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# The built React app (frontend/dist). WhiteNoise serves its assets; config.views.spa serves
# index.html for every page route, so the site and the API share one domain.
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
if FRONTEND_DIST.is_dir():
    WHITENOISE_ROOT = FRONTEND_DIST


def _is_immutable(path, url):
    # Vite puts content-hashed files under /assets/; Django's manifest adds 12-hex-digit hashes.
    return url.startswith("/assets/") or re.match(r"^.+\.[0-9a-f]{12}\..+$", url) is not None


WHITENOISE_IMMUTABLE_FILE_TEST = _is_immutable

# Uploaded files (property images)

MEDIA_URL = "media/"
MEDIA_ROOT = env("MEDIA_ROOT", default=str(BASE_DIR / "media"))

# Production photo storage, in order of preference:
#  1. An S3-compatible bucket (AWS S3, Cloudflare R2, ...): set AWS_STORAGE_BUCKET_NAME and friends.
#  2. A persistent disk (e.g. a Railway volume) at MEDIA_ROOT, with SERVE_MEDIA=True.
# Without either, uploads live on the container's disk and vanish on redeploy.
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", default="")
if AWS_STORAGE_BUCKET_NAME:
    STORAGES["default"] = {"BACKEND": "storages.backends.s3.S3Storage"}
    AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL", default=None)  # Needed for R2 and other non-AWS hosts.
    AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default=None)
    AWS_S3_CUSTOM_DOMAIN = env("AWS_S3_CUSTOM_DOMAIN", default=None)  # A public URL for the bucket, if any.
    AWS_QUERYSTRING_AUTH = AWS_S3_CUSTOM_DOMAIN is None  # Signed URLs unless the bucket is public.
    AWS_S3_FILE_OVERWRITE = False
    # AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are read from the environment by boto3.
SERVE_MEDIA = env.bool("SERVE_MEDIA", default=False)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Logging: everything to stdout, where hosting platforms collect it.

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "{asctime} {levelname} {name}: {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", default="INFO")},
}


# Production security (only when DEBUG is off)

if not DEBUG:
    # Hosting platforms terminate HTTPS at a proxy and forward plain HTTP.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
    # Platform health checks call over plain HTTP from inside the network.
    SECURE_REDIRECT_EXEMPT = [r"^api/health/$"]
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # Start low; raise to 31536000 (1 year) once HTTPS is confirmed working.
    SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=3600)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True)

# HSTS preload is a long-term commitment for a whole domain; opt in deliberately.
SILENCED_SYSTEM_CHECKS = ["security.W021"]
