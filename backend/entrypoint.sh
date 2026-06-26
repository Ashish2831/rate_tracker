#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
until python -c "import psycopg2; psycopg2.connect(dbname='${POSTGRES_DB}', user='${POSTGRES_USER}', password='${POSTGRES_PASSWORD}', host='${POSTGRES_HOST}')" 2>/dev/null; do
  sleep 1
done

echo "Running migrations..."
python manage.py migrate --noinput

exec "$@"
