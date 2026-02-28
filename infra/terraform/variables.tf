variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-southeast-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "factory-insider"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

# VPC Variables
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["ap-southeast-1a", "ap-southeast-1b"]
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnets"
  type        = bool
  default     = true
}

variable "enable_vpc_endpoints" {
  description = "Enable VPC endpoints for S3 and DynamoDB"
  type        = bool
  default     = true
}

# RDS Variables
variable "rds_engine_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "16.1"
}

variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t4g.micro"
}

variable "rds_allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 20
}

variable "rds_database_name" {
  description = "Initial database name"
  type        = string
  default     = "factory_insider"
}

variable "rds_master_username" {
  description = "Master username for RDS"
  type        = string
  sensitive   = true
}

variable "rds_master_password" {
  description = "Master password for RDS"
  type        = string
  sensitive   = true
}

variable "rds_enable_backup" {
  description = "Enable automated backups"
  type        = bool
  default     = true
}

variable "rds_backup_retention_period" {
  description = "Backup retention period in days"
  type        = number
  default     = 7
}

variable "rds_enable_encryption" {
  description = "Enable storage encryption"
  type        = bool
  default     = true
}

variable "rds_multi_az" {
  description = "Enable Multi-AZ deployment"
  type        = bool
  default     = false
}

variable "rds_publicly_accessible" {
  description = "Make RDS instance publicly accessible"
  type        = bool
  default     = false
}

# ElastiCache Variables
variable "elasticache_engine_version" {
  description = "Redis engine version"
  type        = string
  default     = "7.0"
}

variable "elasticache_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t4g.micro"
}

variable "elasticache_num_cache_nodes" {
  description = "Number of cache nodes"
  type        = number
  default     = 1
}

variable "elasticache_parameter_group_name" {
  description = "Parameter group name"
  type        = string
  default     = "default.redis7"
}

variable "elasticache_automatic_failover" {
  description = "Enable automatic failover"
  type        = bool
  default     = false
}

variable "elasticache_automatic_backup" {
  description = "Enable automatic backup"
  type        = bool
  default     = true
}

variable "elasticache_snapshot_retention" {
  description = "Snapshot retention period in days"
  type        = number
  default     = 5
}

# S3 Variables
variable "s3_create_buckets" {
  description = "Create S3 buckets"
  type        = bool
  default     = true
}

variable "s3_enable_versioning" {
  description = "Enable versioning on S3 buckets"
  type        = bool
  default     = true
}

variable "s3_enable_encryption" {
  description = "Enable encryption on S3 buckets"
  type        = bool
  default     = true
}

variable "s3_enable_public_access" {
  description = "Enable public access to S3 buckets"
  type        = bool
  default     = false
}

variable "s3_bucket_prefix" {
  description = "Prefix for S3 bucket names"
  type        = string
  default     = "factory-insider"
}

# ECS Variables
variable "ecs_instance_type" {
  description = "ECS instance type"
  type        = string
  default     = "t3.micro"
}

variable "ecs_desired_capacity" {
  description = "Desired number of EC2 instances"
  type        = number
  default     = 2
}

variable "ecs_min_capacity" {
  description = "Minimum number of EC2 instances"
  type        = number
  default     = 1
}

variable "ecs_max_capacity" {
  description = "Maximum number of EC2 instances"
  type        = number
  default     = 4
}

variable "ecs_container_image" {
  description = "Container image for ECS tasks"
  type        = string
}

variable "ecs_container_port" {
  description = "Container port"
  type        = number
  default     = 8000
}

variable "ecs_container_cpu" {
  description = "Container CPU units"
  type        = number
  default     = 256
}

variable "ecs_container_memory" {
  description = "Container memory in MB"
  type        = number
  default     = 512
}

variable "ecs_environment_variables" {
  description = "Environment variables for ECS tasks"
  type        = map(string)
  default     = {}
}

# CloudWatch Variables
variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}
