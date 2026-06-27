#!/usr/bin/env bash
# Build, push backend + frontend images to ECR, then roll ECS services.
set -euo pipefail

AWS_REGION="${AWS_REGION:-ap-south-1}"
ECS_CLUSTER="${ECS_CLUSTER:-rate-tracker-prod-cluster}"
ECS_NAME_PREFIX="${ECS_NAME_PREFIX:-rate-tracker-prod}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
DOCKER_PLATFORM="${DOCKER_PLATFORM:-linux/amd64}"

ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
BACKEND="${ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECS_NAME_PREFIX}-backend"
FRONTEND="${ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECS_NAME_PREFIX}-frontend"

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

echo "Logging in to ECR..."
echo "Building for platform: ${DOCKER_PLATFORM} (ECS Fargate requires linux/amd64)"
aws ecr get-login-password --region "${AWS_REGION}" | \
  docker login --username AWS --password-stdin "${ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "Building backend -> ${BACKEND}:${IMAGE_TAG}"
docker build --platform "${DOCKER_PLATFORM}" -t "${BACKEND}:${IMAGE_TAG}" "${ROOT}/backend"
docker push "${BACKEND}:${IMAGE_TAG}"

echo "Building frontend -> ${FRONTEND}:${IMAGE_TAG}"
docker build --platform "${DOCKER_PLATFORM}" \
  --build-arg NEXT_PUBLIC_API_URL=/api \
  -t "${FRONTEND}:${IMAGE_TAG}" "${ROOT}/frontend"
docker push "${FRONTEND}:${IMAGE_TAG}"

echo "Rolling ECS services..."
ECS_CLUSTER="${ECS_CLUSTER}" \
ECS_NAME_PREFIX="${ECS_NAME_PREFIX}" \
ECR_BACKEND_REPO="${BACKEND}" \
ECR_FRONTEND_REPO="${FRONTEND}" \
IMAGE_TAG="${IMAGE_TAG}" \
AWS_REGION="${AWS_REGION}" \
"${ROOT}/scripts/aws/deploy-ecs.sh"

echo "Done. Health check:"
echo "  curl http://\$(terraform -chdir=${ROOT}/infra/terraform output -raw alb_dns_name)/api/health/"
