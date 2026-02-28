terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Configure backend for state management
  # Uncomment and configure for production
  # backend "s3" {
  #   bucket         = "factory-insider-terraform-state"
  #   key            = "prod/terraform.tfstate"
  #   region         = "ap-southeast-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-locks"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = var.environment
      Project     = var.project_name
      CreatedBy   = "Terraform"
      CreatedAt   = timestamp()
    }
  }
}

# VPC
module "vpc" {
  source = "./modules/vpc"

  project_name           = var.project_name
  environment            = var.environment
  vpc_cidr               = var.vpc_cidr
  availability_zones     = var.availability_zones
  enable_nat_gateway     = var.enable_nat_gateway
  enable_vpc_endpoints   = var.enable_vpc_endpoints
}

# RDS PostgreSQL
module "rds" {
  source = "./modules/rds"

  project_name            = var.project_name
  environment             = var.environment
  engine_version          = var.rds_engine_version
  instance_class          = var.rds_instance_class
  allocated_storage        = var.rds_allocated_storage
  database_name           = var.rds_database_name
  master_username         = var.rds_master_username
  master_password         = var.rds_master_password
  vpc_id                  = module.vpc.vpc_id
  db_subnet_group_name    = module.vpc.db_subnet_group_name
  security_group_ids      = [aws_security_group.rds.id]
  enable_backup           = var.rds_enable_backup
  backup_retention_period = var.rds_backup_retention_period
  enable_encryption       = var.rds_enable_encryption
  multi_az                = var.rds_multi_az
  publicly_accessible     = var.rds_publicly_accessible

  depends_on = [module.vpc]
}

# ElastiCache Redis
module "elasticache" {
  source = "./modules/elasticache"

  project_name          = var.project_name
  environment           = var.environment
  engine_version        = var.elasticache_engine_version
  node_type             = var.elasticache_node_type
  num_cache_nodes       = var.elasticache_num_cache_nodes
  parameter_group_name  = var.elasticache_parameter_group_name
  vpc_id                = module.vpc.vpc_id
  subnet_group_name     = module.vpc.elasticache_subnet_group_name
  security_group_ids    = [aws_security_group.elasticache.id]
  automatic_failover    = var.elasticache_automatic_failover
  automatic_backup      = var.elasticache_automatic_backup
  snapshot_retention    = var.elasticache_snapshot_retention

  depends_on = [module.vpc]
}

# S3 Buckets
module "s3" {
  source = "./modules/s3"

  project_name            = var.project_name
  environment             = var.environment
  create_buckets          = var.s3_create_buckets
  enable_versioning       = var.s3_enable_versioning
  enable_encryption       = var.s3_enable_encryption
  enable_public_access    = var.s3_enable_public_access
  bucket_prefix           = var.s3_bucket_prefix
}

# Security Groups
resource "aws_security_group" "rds" {
  name        = "${var.project_name}-${var.environment}-rds-sg"
  description = "Security group for RDS database"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-rds-sg"
  }
}

resource "aws_security_group" "elasticache" {
  name        = "${var.project_name}-${var.environment}-elasticache-sg"
  description = "Security group for ElastiCache Redis"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-elasticache-sg"
  }
}

resource "aws_security_group" "ecs" {
  name        = "${var.project_name}-${var.environment}-ecs-sg"
  description = "Security group for ECS tasks"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-ecs-sg"
  }
}

# ECS Cluster
module "ecs" {
  source = "./modules/ecs"

  project_name           = var.project_name
  environment            = var.environment
  vpc_id                 = module.vpc.vpc_id
  private_subnet_ids     = module.vpc.private_subnet_ids
  security_group_ids     = [aws_security_group.ecs.id]
  ecs_instance_type      = var.ecs_instance_type
  ecs_desired_capacity   = var.ecs_desired_capacity
  ecs_min_capacity       = var.ecs_min_capacity
  ecs_max_capacity       = var.ecs_max_capacity
  container_image        = var.ecs_container_image
  container_port         = var.ecs_container_port
  container_cpu          = var.ecs_container_cpu
  container_memory       = var.ecs_container_memory
  environment_variables  = var.ecs_environment_variables
}

# CloudWatch Logs
resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/aws/ecs/${var.project_name}-${var.environment}"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${var.project_name}-${var.environment}-logs"
  }
}
