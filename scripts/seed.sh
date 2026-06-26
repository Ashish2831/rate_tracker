#!/bin/bash
set -euo pipefail

docker compose exec backend python manage.py seed_data "$@"
