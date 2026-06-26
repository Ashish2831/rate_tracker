#!/bin/bash
set -euo pipefail

docker compose exec backend pytest "$@"
