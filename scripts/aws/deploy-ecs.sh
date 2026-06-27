#!/usr/bin/env bash
# Roll ECS services to new ECR images (used by GitHub Actions deploy workflow).
set -euo pipefail

: "${AWS_REGION:?AWS_REGION required}"
: "${ECS_CLUSTER:?ECS_CLUSTER required}"
: "${IMAGE_TAG:?IMAGE_TAG required}"
: "${ECR_BACKEND_REPO:?ECR_BACKEND_REPO required}"
: "${ECR_FRONTEND_REPO:?ECR_FRONTEND_REPO required}"

BACKEND_IMAGE="${ECR_BACKEND_REPO}:${IMAGE_TAG}"
FRONTEND_IMAGE="${ECR_FRONTEND_REPO}:${IMAGE_TAG}"

update_service() {
  local service_name="$1"
  local container_name="$2"
  local image_uri="$3"

  echo "Updating ${service_name} (${container_name}) -> ${image_uri}"

  local task_def_arn
  task_def_arn="$(aws ecs describe-services \
    --region "${AWS_REGION}" \
    --cluster "${ECS_CLUSTER}" \
    --services "${service_name}" \
    --query 'services[0].taskDefinition' \
    --output text)"

  local new_task_def
  new_task_def="$(aws ecs describe-task-definition \
    --region "${AWS_REGION}" \
    --task-definition "${task_def_arn}" \
    --query 'taskDefinition' \
    --output json | jq \
      --arg IMAGE "${image_uri}" \
      --arg CONTAINER "${container_name}" \
      'del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)
       | .containerDefinitions = [.containerDefinitions[]
         | if .name == $CONTAINER then .image = $IMAGE else . end]')"

  local new_arn
  new_arn="$(aws ecs register-task-definition \
    --region "${AWS_REGION}" \
    --cli-input-json "${new_task_def}" \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text)"

  aws ecs update-service \
    --region "${AWS_REGION}" \
    --cluster "${ECS_CLUSTER}" \
    --service "${service_name}" \
    --task-definition "${new_arn}" \
    --force-new-deployment \
    --output text >/dev/null

  echo "  Registered ${new_arn}"
}

PREFIX="${ECS_NAME_PREFIX:-rate-tracker-prod}"

update_service "${PREFIX}-backend" "backend" "${BACKEND_IMAGE}"
update_service "${PREFIX}-celery-worker" "celery-worker" "${BACKEND_IMAGE}"
update_service "${PREFIX}-celery-beat" "celery-beat" "${BACKEND_IMAGE}"
update_service "${PREFIX}-frontend" "frontend" "${FRONTEND_IMAGE}"

echo "Waiting for backend service to stabilize..."
aws ecs wait services-stable \
  --region "${AWS_REGION}" \
  --cluster "${ECS_CLUSTER}" \
  --services "${PREFIX}-backend" "${PREFIX}-frontend"

echo "Deploy complete."
