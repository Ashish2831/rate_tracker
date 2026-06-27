variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "rate-tracker"
}

variable "environment" {
  description = "Environment name (e.g. prod, staging)"
  type        = string
  default     = "prod"
}

variable "github_repository" {
  description = "GitHub repo in org/name format for OIDC deploy role trust"
  type        = string
}

variable "domain_name" {
  description = "Optional custom domain for the ALB (leave empty to use ALB DNS name)"
  type        = string
  default     = ""
}

variable "image_tag" {
  description = "Docker image tag for backend and frontend ECR images"
  type        = string
  default     = "latest"
}

variable "db_name" {
  type    = string
  default = "rate_tracker"
}

variable "db_username" {
  type    = string
  default = "rate_tracker"
}

variable "seed_object_key" {
  description = "S3 object key for the seed parquet file"
  type        = string
  default     = "rates_seed.parquet"
}

variable "backend_cpu" {
  type    = number
  default = 512
}

variable "backend_memory" {
  type    = number
  default = 1024
}

variable "frontend_cpu" {
  type    = number
  default = 256
}

variable "frontend_memory" {
  type    = number
  default = 512
}
