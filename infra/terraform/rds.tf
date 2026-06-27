resource "random_password" "db" {
  length  = 32
  special = false
}

resource "random_password" "django_secret" {
  length  = 50
  special = true
}

resource "random_password" "ingest_token" {
  length  = 32
  special = false
}

resource "aws_secretsmanager_secret" "app" {
  name = "${local.name_prefix}/app"
}

resource "aws_secretsmanager_secret_version" "app" {
  secret_id = aws_secretsmanager_secret.app.id
  secret_string = jsonencode({
    DJANGO_SECRET_KEY   = random_password.django_secret.result
    POSTGRES_PASSWORD   = random_password.db.result
    INGEST_BEARER_TOKEN = random_password.ingest_token.result
  })
}

resource "aws_db_subnet_group" "postgres" {
  name       = "${local.name_prefix}-postgres"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_db_instance" "postgres" {
  identifier                 = "${local.name_prefix}-postgres"
  engine                     = "postgres"
  engine_version             = "16"
  instance_class             = "db.t4g.micro"
  allocated_storage          = 20
  db_name                    = var.db_name
  username                   = var.db_username
  password                   = random_password.db.result
  db_subnet_group_name       = aws_db_subnet_group.postgres.name
  vpc_security_group_ids     = [aws_security_group.rds.id]
  publicly_accessible        = false
  skip_final_snapshot        = true
  backup_retention_period    = 1
  auto_minor_version_upgrade = true
  storage_encrypted          = true
}
