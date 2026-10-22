"""Shared demo accounts, created by `manage.py seed_demo` for portfolio and review sites."""

DEMO_DOMAIN = "demo.keyhouse.test"
DEMO_PASSWORD = "Keyhouse-demo-2026"

# The accounts the "Try the demo" buttons log in as.
DEMO_LOGINS = {
    "guest": f"guest@{DEMO_DOMAIN}",
    "host": f"amara@{DEMO_DOMAIN}",
}

DEMO_READ_ONLY_MESSAGE = (
    "The demo accounts are shared, so editing listings, photos and profiles is turned off. "
    "Create your own account to try it."
)


def is_demo_email(email):
    return email.lower().endswith(f"@{DEMO_DOMAIN}")
