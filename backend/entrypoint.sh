#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
until python -c "import psycopg2; psycopg2.connect(dbname='${POSTGRES_DB}', user='${POSTGRES_USER}', password='${POSTGRES_PASSWORD}', host='${POSTGRES_HOST}')" 2>/dev/null; do
  sleep 1
done

if [ -n "${SEED_S3_URI:-}" ] && [ ! -f "${SEED_PARQUET_PATH}" ]; then
  echo "Downloading seed parquet from ${SEED_S3_URI}..."
  mkdir -p "$(dirname "${SEED_PARQUET_PATH}")"
  python - <<'PY'
import os
import boto3

uri = os.environ["SEED_S3_URI"]
path = os.environ["SEED_PARQUET_PATH"]
bucket, key = uri.replace("s3://", "", 1).split("/", 1)
boto3.client("s3").download_file(bucket, key, path)
print(f"Downloaded seed data to {path}")
PY
fi

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  echo "Running migrations..."
  python manage.py migrate --noinput
fi

# Build dbt marts when missing (fresh RDS / first deploy). No-op if tables already exist.
if [ "${RUN_DBT_ON_STARTUP:-true}" = "true" ]; then
  echo "Ensuring dbt analytics marts exist..."
  python manage.py run_dbt --if-missing || echo "WARNING: dbt bootstrap failed — run 'manage.py seed_data' manually"
fi

echo "Collecting static files..."
python manage.py collectstatic --noinput

exec "$@"
