#!/usr/bin/env bash
# One-time bootstrap for Terraform remote state (run with AWS admin credentials).
#
# Override names if needed:
#   TF_STATE_BUCKET=my-custom-tfstate-bucket
#   TF_LOCK_TABLE=my-custom-terraform-locks
#   PROJECT_NAME=rate-tracker
#   AWS_REGION=ap-south-1
set -euo pipefail

export AWS_PAGER=""

REGION="${AWS_REGION:-ap-south-1}"
PROJECT="${PROJECT_NAME:-rate-tracker}"
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
REGION_SLUG="${REGION//-/_}"

# Default includes region to avoid clashes with stuck/deleted buckets in other regions.
BUCKET="${TF_STATE_BUCKET:-${PROJECT}-tfstate-${REGION}-${ACCOUNT_ID}}"
LOCK_TABLE="${TF_LOCK_TABLE:-${PROJECT}-tf-locks-${REGION_SLUG}}"

bucket_exists() {
  aws s3api head-bucket --bucket "${BUCKET}" --region "${REGION}" 2>/dev/null
}

create_bucket_with_retry() {
  local attempt
  for attempt in $(seq 1 6); do
    if bucket_exists; then
      echo "Bucket already exists: ${BUCKET}"
      return 0
    fi

    echo "Creating S3 bucket: ${BUCKET} (attempt ${attempt}/6)"
    set +e
    if [ "${REGION}" = "us-east-1" ]; then
      output="$(aws s3api create-bucket --bucket "${BUCKET}" --region "${REGION}" 2>&1)"
    else
      output="$(aws s3api create-bucket --bucket "${BUCKET}" --region "${REGION}" \
        --create-bucket-configuration "LocationConstraint=${REGION}" 2>&1)"
    fi
    status=$?
    set -e

    if [ "${status}" -eq 0 ]; then
      echo "Bucket created."
      return 0
    fi

    if echo "${output}" | grep -q "BucketAlreadyOwnedByYou\|BucketAlreadyExists"; then
      echo "Bucket already exists: ${BUCKET}"
      return 0
    fi

    if echo "${output}" | grep -q "OperationAborted"; then
      echo "AWS is still finishing a previous bucket operation — waiting before retry..."
      sleep $((attempt * 10))
      continue
    fi

    echo "${output}" >&2
    return "${status}"
  done

  echo "Failed to create bucket after 6 attempts." >&2
  echo "Try a custom name: TF_STATE_BUCKET=your-unique-name-${ACCOUNT_ID} AWS_REGION=${REGION} $0" >&2
  return 1
}

configure_bucket() {
  aws s3api put-bucket-versioning --bucket "${BUCKET}" --region "${REGION}" \
    --versioning-configuration Status=Enabled
  aws s3api put-bucket-encryption --bucket "${BUCKET}" --region "${REGION}" \
    --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
}

create_bucket_with_retry
configure_bucket

echo "Creating DynamoDB lock table: ${LOCK_TABLE}"
if aws dynamodb describe-table --table-name "${LOCK_TABLE}" --region "${REGION}" >/dev/null 2>&1; then
  echo "Lock table already exists"
else
  aws dynamodb create-table \
    --table-name "${LOCK_TABLE}" \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region "${REGION}" \
    --output text >/dev/null
  echo "Waiting for lock table to become active..."
  aws dynamodb wait table-exists --table-name "${LOCK_TABLE}" --region "${REGION}"
fi

cat <<EOF

Bootstrap complete. Initialize Terraform with:

  cd infra/terraform
  terraform init \\
    -backend-config="bucket=${BUCKET}" \\
    -backend-config="key=prod/terraform.tfstate" \\
    -backend-config="region=${REGION}" \\
    -backend-config="dynamodb_table=${LOCK_TABLE}" \\
    -backend-config="encrypt=true"

Add these GitHub repository variables/secrets for deploy workflow:
  TF_STATE_BUCKET=${BUCKET}
  TF_STATE_REGION=${REGION}
  TF_STATE_LOCK_TABLE=${LOCK_TABLE}

EOF
