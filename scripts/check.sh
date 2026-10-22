#!/bin/sh
# Run the same checks as CI (.github/workflows/ci.yml) before pushing.
# Usage: sh scripts/check.sh   (from the project root, with the virtualenv active)
set -e

echo "==> Lint"
ruff check .
ruff format --check .

echo "==> Missing migrations"
python manage.py makemigrations --check --dry-run

echo "==> Tests (DEBUG=False, as in CI)"
DEBUG=False pytest -q

echo "==> Production settings"
DEBUG=False \
  SECRET_KEY=local-check-a-long-random-looking-string-not-used-anywhere-else-1234567890 \
  ALLOWED_HOSTS=example.com \
  python manage.py check --deploy --fail-level WARNING

echo "==> Frontend type-check and build"
(cd frontend && npm run build >/dev/null)

echo "All checks passed."
