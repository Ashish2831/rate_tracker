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

## Operations

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
| `backend/rates/api/health.py` | ALB health check endpoint |
