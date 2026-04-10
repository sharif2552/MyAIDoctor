#!/usr/bin/env sh
# Run Alembic inside the backend container with correct PYTHONPATH and config.
# Usage:
#   docker compose exec backend sh scripts/alembic-docker.sh upgrade head
#   docker compose exec backend sh scripts/alembic-docker.sh current
#
# If the database was created before Alembic (tables exist, upgrade fails with DuplicateTable):
#   docker compose exec backend sh scripts/alembic-docker.sh stamp 0001_init
#   docker compose exec backend sh scripts/alembic-docker.sh upgrade head
set -e
export PYTHONPATH=/app
cd /app
exec alembic -c alembic.ini "$@"
