#!/bin/sh
# Container start command for hosts without a separate pre-deploy step (e.g. Render's free plan).
set -e

python manage.py migrate --noinput
python manage.py ensure_superuser
if [ "$SEED_DEMO" = "True" ]; then
  python manage.py seed_demo
fi

exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --access-logfile -
