#!/bin/bash
set -euo pipefail

docker compose exec backend pytest "$@"
docker compose exec frontend npm test
