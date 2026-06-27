output "alb_dns_name" {
  description = "Public ALB DNS name — open http://<this> in a browser"
  value       = aws_lb.main.dns_name
}

output "app_url" {
  description = "Application URL (dashboard + API on same host)"
  value       = local.app_url
}

output "api_url" {
  description = "API base URL"
  value       = "${local.app_url}/api"
}

output "ecr_backend_repository_url" {
  value = aws_ecr_repository.backend.repository_url
}

output "ecr_frontend_repository_url" {
  value = aws_ecr_repository.frontend.repository_url
}

output "seed_bucket_name" {
  description = "Upload rates_seed.parquet here before first ingest"
  value       = aws_s3_bucket.seed.id
}

output "github_actions_role_arn" {
  description = "Add this as GitHub secret AWS_ROLE_ARN"
  value       = aws_iam_role.github_actions.arn
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
}

output "rds_endpoint" {
  value     = aws_db_instance.postgres.address
  sensitive = true
}
