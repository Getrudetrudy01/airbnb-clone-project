# --- Stage 1: build the React frontend ----------------------------------------
FROM node:24-slim AS frontend

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build


# --- Stage 2: the Django app, which also serves the built frontend --------------
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Build dependencies for mysqlclient
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential default-libmysqlclient-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# base.txt for production images; docker-compose passes dev.txt for local development.
ARG REQUIREMENTS=base.txt
COPY requirements/ requirements/
RUN pip install -r requirements/${REQUIREMENTS}

COPY . .
COPY --from=frontend /frontend/dist /app/frontend/dist

# Static files are baked into the image; the key is only needed for Django to start.
RUN SECRET_KEY=collectstatic-only python manage.py collectstatic --noinput

# Don't run as root. (A Railway volume mounts as root: see docs/deploy-railway.md.)
RUN useradd --create-home appuser && mkdir -p /app/media && chown -R appuser /app/media
USER appuser

EXPOSE 8000
# Railway runs migrations as a pre-deploy step (railway.json); Render uses scripts/start.sh instead.
CMD ["sh", "-c", "gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${WEB_CONCURRENCY:-3} --access-logfile -"]
