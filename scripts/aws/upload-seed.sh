#!/usr/bin/env bash
# Upload seed parquet to the Terraform-managed S3 bucket.
set -euo pipefail

: "${SEED_BUCKET:?SEED_BUCKET required — run: terraform output -raw seed_bucket_name}"
: "${SEED_FILE:?SEED_FILE required — path to rates_seed.parquet}"

KEY="${SEED_OBJECT_KEY:-rates_seed.parquet}"

echo "Uploading ${SEED_FILE} -> s3://${SEED_BUCKET}/${KEY}"
aws s3 cp "${SEED_FILE}" "s3://${SEED_BUCKET}/${KEY}"
echo "Done. Celery beat or 'manage.py seed_data' will pick it up on next run."
