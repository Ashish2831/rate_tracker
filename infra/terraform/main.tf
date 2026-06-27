terraform {
  required_version = ">= 1.6.0"

  backend "s3" {}

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

data "aws_caller_identity" "current" {}
data "aws_availability_zones" "available" { state = "available" }

locals {
  name_prefix = "${var.project_name}-${var.environment}"
  azs         = slice(data.aws_availability_zones.available.names, 0, 2)

  app_url = var.domain_name != "" ? "https://${var.domain_name}" : "http://${aws_lb.main.dns_name}"

  backend_image  = "${aws_ecr_repository.backend.repository_url}:${var.image_tag}"
  frontend_image = "${aws_ecr_repository.frontend.repository_url}:${var.image_tag}"

  common_backend_env = [
    { name = "POSTGRES_DB", value = var.db_name },
    { name = "POSTGRES_USER", value = var.db_username },
    { name = "POSTGRES_HOST", value = aws_db_instance.postgres.address },
    { name = "POSTGRES_PORT", value = "5432" },
    { name = "REDIS_URL", value = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:6379/0" },
    { name = "DJANGO_DEBUG", value = "false" },
    { name = "DJANGO_ALLOWED_HOSTS", value = join(",", compact([aws_lb.main.dns_name, var.domain_name, "localhost", "*"])) },
    { name = "CORS_ALLOWED_ORIGINS", value = local.app_url },
    { name = "SEED_PARQUET_PATH", value = "/data/rates_seed.parquet" },
    { name = "SEED_S3_URI", value = "s3://${aws_s3_bucket.seed.id}/${var.seed_object_key}" },
    { name = "SLOW_QUERY_THRESHOLD_MS", value = "200" },
    { name = "LOG_LEVEL", value = "INFO" },
  ]

  common_backend_secrets = [
    { name = "DJANGO_SECRET_KEY", valueFrom = "${aws_secretsmanager_secret.app.arn}:DJANGO_SECRET_KEY::" },
    { name = "POSTGRES_PASSWORD", valueFrom = "${aws_secretsmanager_secret.app.arn}:POSTGRES_PASSWORD::" },
    { name = "INGEST_BEARER_TOKEN", valueFrom = "${aws_secretsmanager_secret.app.arn}:INGEST_BEARER_TOKEN::" },
  ]
}
