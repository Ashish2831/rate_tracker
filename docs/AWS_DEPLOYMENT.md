# AWS Deployment Guide

Deploy Rate Tracker to **AWS ECS Fargate** with **RDS PostgreSQL**, **ElastiCache Redis**, **Application Load Balancer**, and **GitHub Actions** CI/CD.

## Architecture

```
                         INTERNET
                            │
                            ▼
              ┌─────────────────────────┐
              │  Application Load       │
              │  Balancer  (HTTP :80)   │
              └───┬─────────────────┬───┘
                  │                 │
         /api/*   │                 │  /*
         /admin/* │                 │
                  ▼                 ▼
         ┌──────────────┐   ┌──────────────┐
         │ ECS Fargate  │   │ ECS Fargate  │
         │   backend    │   │   frontend   │
         │  Django:8000 │   │  Next.js:3000│
         └──────┬───────┘   └──────────────┘
                │
    ┌───────────┼───────────┬──────────────────┐
    │           │           │                  │
    ▼           ▼           ▼                  ▼
┌────────┐ ┌────────┐ ┌──────────┐    ┌──────────────┐
│ celery │ │ celery │ │   RDS    │    │ ElastiCache  │
│ worker │ │  beat  │ │ Postgres │    │    Redis     │
└────────┘ └────────┘ └──────────┘    └──────────────┘
         PRIVATE SUBNETS

S3 ── seed parquet          Secrets Manager ── app secrets
ECR ── Docker images        CloudWatch ── logs
GitHub Actions ── build + deploy pipeline
```

**Estimated cost:** ~$80–120/month (NAT gateway, RDS, ElastiCache, Fargate × 4). Tear down with `terraform destroy` when not needed.

---

## Prerequisites

- AWS account with admin access (first-time bootstrap only)
- [AWS CLI](https://aws.amazon.com/cli/) v2 configured for **`ap-south-1` (Mumbai)**:

  ```bash
  aws configure set region ap-south-1
  ```

- [Terraform](https://www.terraform.io/downloads) ≥ 1.6
- GitHub repository with Actions enabled
- Seed file: `data/rates_seed.parquet`

---

## Step 1 — Bootstrap Terraform state

```bash
chmod +x scripts/aws/bootstrap-state.sh
AWS_REGION=ap-south-1 ./scripts/aws/bootstrap-state.sh
```

Default bucket name: `rate-tracker-tfstate-ap-south-1-<account-id>`.  
To use a custom name (e.g. if a previous create got stuck):

```bash
TF_STATE_BUCKET=ashish-rate-tracker-tfstate AWS_REGION=ap-south-1 ./scripts/aws/bootstrap-state.sh
```

Follow the printed `terraform init` command (S3 bucket + DynamoDB lock table).

> **New machine / clone:** You must run `terraform init` with `-backend-config=...` before every `plan` or `apply`. If you see `Backend initialization required`, run init again — it does not run automatically.

Example (replace bucket/table with bootstrap output or `rate-tracker-tfstate-ap-south-1-<account-id>`):

```bash
terraform init \
  -backend-config="bucket=rate-tracker-tfstate-ap-south-1-$(aws sts get-caller-identity --query Account --output text)" \
  -backend-config="key=prod/terraform.tfstate" \
  -backend-config="region=ap-south-1" \
  -backend-config="dynamodb_table=rate-tracker-tf-locks-ap_south_1" \
  -backend-config="encrypt=true"
```

---

## Step 2 — Provision infrastructure

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars — set github_repository to "your-org/Rate_Tracker"

terraform init \
  -backend-config="bucket=YOUR_STATE_BUCKET" \
  -backend-config="key=prod/terraform.tfstate" \
  -backend-config="region=ap-south-1" \
  -backend-config="dynamodb_table=YOUR_LOCK_TABLE" \
  -backend-config="encrypt=true"

terraform plan
terraform apply
```

Save outputs:

```bash
terraform output alb_dns_name
terraform output github_actions_role_arn
terraform output seed_bucket_name
```

---

## Step 3 — Upload seed data

```bash
SEED_BUCKET=$(terraform output -raw seed_bucket_name)
SEED_FILE=../../data/rates_seed.parquet ./scripts/aws/upload-seed.sh
```

---

## Step 4 — Push initial Docker images

Before the first deploy, ECR repositories are empty. Either:

**Option A — GitHub Actions:** Add secrets/variables (Step 5), then run **Deploy** workflow manually (`workflow_dispatch`).

**Option B — Local push (recommended):**

```bash
AWS_REGION=ap-south-1 ./scripts/aws/push-images.sh
```

This logs in to ECR, builds/pushes both images, and rolls ECS services.

> **zsh note:** Never use `$BACKEND:latest` — zsh treats that as variable `BACKENDatest`. Always use `"${BACKEND}:latest"` or use the script above.

---

## Step 5 — Configure GitHub Actions

Add **`AWS_ROLE_ARN`** in **one** of these places (the Deploy workflow uses the `AWS_CI_CD` environment):

| Where | Path |
|-------|------|
| **Environment secret (recommended)** | Settings → Environments → **AWS_CI_CD** → Environment secrets |
| Repository secret | Settings → Secrets and variables → Actions → Repository secrets |

| Name | Value |
|------|-------|
| `AWS_ROLE_ARN` | `terraform output -raw github_actions_role_arn` |

Optional **repository variables** (Settings → Actions → Variables):

| Name | Value |
|------|-------|
| `AWS_REGION` | `ap-south-1` |
| `ECS_CLUSTER` | `rate-tracker-prod-cluster` |
| `ECS_NAME_PREFIX` | `rate-tracker-prod` |
| `ALB_DNS_NAME` | `terraform output -raw alb_dns_name` (optional, for smoke test) |

---

## Step 6 — CI/CD flow

| Workflow | Trigger | Action |
|----------|---------|--------|
| **CI** | Push/PR to `main` | Tests (Postgres + Redis), lint, build |
| **Deploy** | CI succeeds on `main`, or manual | Build images → push ECR → roll ECS services → smoke test |

Open the app:

```bash
open "http://$(terraform output -raw alb_dns_name)"
```

API health: `http://<alb-dns>/api/health/`

---

## Step 7 — Load production data (required once)

Uploading parquet to S3 alone does **not** populate the dashboard. The API reads **dbt marts** (`analytics.mart_*`), not raw rows.

After images are deployed and ECS tasks are running:

```bash
# Discover network config from the backend service
NET=$(aws ecs describe-services \
  --cluster rate-tracker-prod-cluster \
  --services rate-tracker-prod-backend \
  --query 'services[0].networkConfiguration.awsvpcConfiguration' \
  --output json)

SUBNETS=$(echo "$NET" | jq -r '.subnets | join(",")')
SG=$(echo "$NET" | jq -r '.securityGroups[0]')

aws ecs run-task \
  --cluster rate-tracker-prod-cluster \
  --task-definition rate-tracker-prod-backend \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNETS],securityGroups=[$SG],assignPublicIp=DISABLED}" \
  --overrides '{"containerOverrides":[{"name":"backend","command":["python","manage.py","seed_data"]}]}'

aws logs tail /ecs/rate-tracker-prod/backend --follow
```

Takes several minutes (~1M raw rows + dbt full refresh). Verify:

```bash
curl "http://$(terraform output -raw alb_dns_name)/api/rates/latest"
```

Re-runs are idempotent (duplicates skipped at raw layer).

---

## Operations

### Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `/api/health/` OK, `/api/rates/*` → **500** | dbt marts missing (`relation "analytics.mart_rates" does not exist`) | Run **Step 7** seed task; ensure backend image includes `/dbt` and `DBT_*` env vars (`terraform apply`) |
| `terraform apply` → backend init error | S3 backend not initialized | Run `terraform init` with `-backend-config` (Step 2) |
| Dashboard empty, APIs return `count: 0` | Marts exist but no seed yet | Run **Step 7** |
| Seed fails: `timezone.utc` / parse errors | Old backend image | Redeploy latest backend image |
| Celery not ingesting | Worker/beat not running or parquet missing | Check `aws logs tail /ecs/rate-tracker-prod/celery-worker --follow` |

CloudWatch error filter:

```bash
aws logs filter-log-events \
  --log-group-name /ecs/rate-tracker-prod/backend \
  --filter-pattern "Internal Server Error" \
  --limit 5
```

### dbt in production

The backend Docker image includes the `dbt/` project at `/dbt`. ECS backend and Celery tasks set `DBT_PROJECT_DIR=/dbt`, `DBT_PROFILES_DIR=/dbt`, and `DBT_RUN_AFTER_INGEST=true`, so `seed_data` and webhook ingest refresh analytics marts automatically.

On container start, `entrypoint.sh` runs `python manage.py run_dbt --if-missing` to create empty mart schemas on a fresh RDS. **You still need to load data once** — APIs read `analytics.mart_*` tables, not raw rows alone.

**First deploy / 500 on `/api/rates/*`:** run a one-off seed task (see below).

### One-off seed (ECS run-task)

When `/api/health/` is OK but rate endpoints return 500 with `relation "analytics.mart_rates" does not exist`, load data (or use **Step 7** above):

```bash
CLUSTER=rate-tracker-prod-cluster
TASK_DEF=rate-tracker-prod-backend

NET=$(aws ecs describe-services --cluster "$CLUSTER" --services rate-tracker-prod-backend \
  --query 'services[0].networkConfiguration.awsvpcConfiguration' --output json)
SUBNETS=$(echo "$NET" | jq -r '.subnets | join(",")')
SG=$(echo "$NET" | jq -r '.securityGroups[0]')

aws ecs run-task \
  --cluster "$CLUSTER" \
  --task-definition "$TASK_DEF" \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNETS],securityGroups=[$SG],assignPublicIp=DISABLED}" \
  --overrides '{"containerOverrides":[{"name":"backend","command":["python","manage.py","seed_data"]}]}'

aws logs tail /ecs/rate-tracker-prod/backend --follow
```

To refresh marts only (raw already loaded): override command with `python manage.py run_dbt --full-refresh`.

Takes several minutes (~1M raw rows + dbt full refresh). Verify:

```bash
curl "http://$(cd infra/terraform && terraform output -raw alb_dns_name)/api/rates/latest"
```

### Pause stack (save cost)

Scale compute to zero and stop RDS when not demoing:

```bash
CLUSTER=rate-tracker-prod-cluster
PREFIX=rate-tracker-prod

for svc in backend frontend celery-worker celery-beat; do
  aws ecs update-service --cluster "$CLUSTER" --service "${PREFIX}-${svc}" --desired-count 0
done

aws rds stop-db-instance --db-instance-identifier "${PREFIX}-postgres"
```

Resume:

```bash
aws rds start-db-instance --db-instance-identifier rate-tracker-prod-postgres
# wait until available, then scale ECS services back to desired-count 1
```

NAT Gateway and ALB still bill (~$50/month) while paused. Full teardown: `terraform destroy`.

### View logs

```bash
aws logs tail /ecs/rate-tracker-prod/backend --follow
aws logs tail /ecs/rate-tracker-prod/celery-worker --follow
```

### Manual seed (one-off ECS exec)

```bash
aws ecs execute-command --cluster rate-tracker-prod-cluster \
  --task TASK_ID --container backend --interactive --command "python manage.py seed_data"
```

(Requires ECS Exec enabled — not configured by default in this stack.)

### Rotate ingest token

Update the secret in Secrets Manager, then redeploy backend/celery services.

### HTTPS + custom domain

1. Request an ACM certificate for your domain (in the same region as the ALB).
2. Add an HTTPS listener on the ALB and redirect HTTP → HTTPS.
3. Create a Route 53 alias record to the ALB.
4. Set `domain_name` in `terraform.tfvars` and re-apply (updates CORS / ALLOWED_HOSTS).

### Tear down

```bash
cd infra/terraform
terraform destroy
```

Also delete the Terraform state S3 bucket and DynamoDB table if no longer needed.

---

## Files reference

| Path | Purpose |
|------|---------|
| `infra/terraform/` | VPC, RDS, Redis, ECS, ALB, ECR, IAM (OIDC) |
| `.github/workflows/ci.yml` | Test pipeline |
| `.github/workflows/deploy.yml` | Build → ECR → ECS rolling deploy |
| `scripts/aws/bootstrap-state.sh` | One-time remote state setup |
| `scripts/aws/deploy-ecs.sh` | ECS task definition rolling update |
| `scripts/aws/upload-seed.sh` | Upload parquet to S3 |
| `backend/Dockerfile` | Built from repo root — includes `dbt/` at `/dbt` |
| `backend/entrypoint.sh` | Migrations + `run_dbt --if-missing` on startup |
| `backend/rates/api/health.py` | ALB health check (Postgres + Redis only) |
| `dbt/` | SQL models — staging, intermediate, analytics marts |
