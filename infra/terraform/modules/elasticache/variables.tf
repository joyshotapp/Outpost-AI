variable "project_name" { type = string }
variable "environment" { type = string }
variable "engine_version" { type = string }
variable "node_type" { type = string }
variable "num_cache_nodes" { type = number }
variable "parameter_group_name" { type = string }
variable "vpc_id" { type = string }
variable "subnet_group_name" { type = string }
variable "security_group_ids" { type = list(string) }
variable "automatic_failover" { type = bool; default = false }
variable "automatic_backup" { type = bool; default = true }
variable "snapshot_retention" { type = number; default = 5 }
