variable "project_name" { type = string }
variable "environment" { type = string }
variable "engine_version" { type = string }
variable "instance_class" { type = string }
variable "allocated_storage" { type = number }
variable "database_name" { type = string }
variable "master_username" { type = string; sensitive = true }
variable "master_password" { type = string; sensitive = true }
variable "db_subnet_group_name" { type = string }
variable "vpc_id" { type = string }
variable "security_group_ids" { type = list(string) }
variable "enable_backup" { type = bool; default = true }
variable "backup_retention_period" { type = number; default = 7 }
variable "enable_encryption" { type = bool; default = true }
variable "multi_az" { type = bool; default = false }
variable "publicly_accessible" { type = bool; default = false }
